import React, { useEffect, useRef } from 'react';
import { throttle } from 'lodash';

interface AudioRecorderProps {
  isListening: boolean;
  onAudioData: (audioData: Float32Array) => void;
}

const API_BASE = process.env.REACT_APP_API_URL || 'https://knowledgeos.onrender.com';
const CHUNK_DURATION = 4000; // 4 seconds in milliseconds
const OVERLAP_DURATION = 2000; // 2 seconds in milliseconds
const SAMPLE_RATE = 16000;
const SEND_INTERVAL = 1000; // Rate limit: send at most once per second

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ isListening, onAudioData }) => {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorNodeRef = useRef<ScriptProcessorNode | null>(null);
  const audioBufferRef = useRef<Float32Array[]>([]);
  const overlapBufferRef = useRef<Float32Array>(new Float32Array(0));
  const lastSendTimeRef = useRef<number>(0);
  
  // Throttled send function to implement rate limiting
  const throttledSendAudio = useRef(
    throttle(async (audioData: Float32Array) => {
      try {
        // Compress audio by downsampling if needed
        const compressed = compressAudio(audioData);
        onAudioData(compressed);
        console.log('Sent audio chunk:', {
          originalSize: audioData.length,
          compressedSize: compressed.length,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error('Error sending audio:', error);
      }
    }, SEND_INTERVAL)
  ).current;

  const compressAudio = (audioData: Float32Array): Float32Array => {
    // Simple compression by downsampling to 16kHz if higher
    const downsampleRatio = Math.floor(audioContextRef.current?.sampleRate ?? SAMPLE_RATE) / SAMPLE_RATE;
    if (downsampleRatio <= 1) return audioData;

    const compressed = new Float32Array(Math.floor(audioData.length / downsampleRatio));
    for (let i = 0; i < compressed.length; i++) {
      compressed[i] = audioData[i * Math.floor(downsampleRatio)];
    }
    return compressed;
  };

  const processAudioChunk = (inputData: Float32Array) => {
    // Add new data to overlap buffer
    const newBuffer = new Float32Array(overlapBufferRef.current.length + inputData.length);
    newBuffer.set(overlapBufferRef.current);
    newBuffer.set(inputData, overlapBufferRef.current.length);
    overlapBufferRef.current = newBuffer;

    // Check if we have enough data for a chunk
    const samplesPerChunk = Math.floor((CHUNK_DURATION / 1000) * SAMPLE_RATE);
    const overlapSamples = Math.floor((OVERLAP_DURATION / 1000) * SAMPLE_RATE);

    while (overlapBufferRef.current.length >= samplesPerChunk) {
      // Extract chunk
      const chunk = overlapBufferRef.current.slice(0, samplesPerChunk);
      
      // Keep overlap portion
      overlapBufferRef.current = overlapBufferRef.current.slice(samplesPerChunk - overlapSamples);
      
      // Send chunk
      throttledSendAudio(chunk);
    }
  };

  useEffect(() => {
    const initializeRecording = async () => {
      try {
        console.log('Initializing audio recording...');
        
        // Request microphone access with specific constraints
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            channelCount: 1,
            sampleRate: SAMPLE_RATE
          }
        });

        streamRef.current = stream;
        
        // Initialize audio context and nodes
        const audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
        audioContextRef.current = audioContext;
        
        const source = audioContext.createMediaStreamSource(stream);
        sourceNodeRef.current = source;
        
        // Create processor node for handling raw audio data
        const processor = audioContext.createScriptProcessor(2048, 1, 1);
        processorNodeRef.current = processor;
        
        // Connect nodes
        source.connect(processor);
        processor.connect(audioContext.destination);
        
        // Handle audio processing
        processor.onaudioprocess = (e) => {
          if (isListening) {
            const inputData = e.inputBuffer.getChannelData(0);
            processAudioChunk(inputData);
          }
        };

        console.log('Audio recording initialized with settings:', {
          sampleRate: SAMPLE_RATE,
          chunkDuration: CHUNK_DURATION,
          overlapDuration: OVERLAP_DURATION,
          rateLimit: SEND_INTERVAL
        });

      } catch (error) {
        console.error('Error initializing audio recording:', error);
      }
    };

    if (isListening) {
      initializeRecording();
    }

    // Cleanup
    return () => {
      if (processorNodeRef.current) {
        processorNodeRef.current.disconnect();
        processorNodeRef.current = null;
      }
      if (sourceNodeRef.current) {
        sourceNodeRef.current.disconnect();
        sourceNodeRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      // Reset buffers
      overlapBufferRef.current = new Float32Array(0);
      audioBufferRef.current = [];
      // Cancel any pending throttled sends
      throttledSendAudio.cancel();
    };
  }, [isListening, throttledSendAudio]);

  return null;
};