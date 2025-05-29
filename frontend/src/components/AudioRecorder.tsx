import React, { useEffect, useRef } from 'react';

interface AudioRecorderProps {
  isListening: boolean;
  onAudioData: (audioData: Float32Array) => void;
}

const API_BASE = process.env.REACT_APP_API_URL || 'https://knowledgeos.onrender.com';
const CHUNK_DURATION = 4; // 4 seconds
const OVERLAP_DURATION = 2; // 2 seconds
const SAMPLE_RATE = 16000;

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ isListening, onAudioData }) => {
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioBufferRef = useRef<Float32Array>(new Float32Array(0));
  const analyserRef = useRef<AnalyserNode | null>(null);

  useEffect(() => {
    const initializeRecording = async () => {
      try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: SAMPLE_RATE
          }
        });
        
        streamRef.current = stream;
        console.log('Recording started - speak now');
        
        // Create audio context
        const audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
        audioContextRef.current = audioContext;
        
        // Create source
        const source = audioContext.createMediaStreamSource(stream);
        sourceRef.current = source;
        
        // Create analyser node
        const analyser = audioContext.createAnalyser();
        analyserRef.current = analyser;
        analyser.fftSize = 2048;
        
        // Create script processor node for handling audio chunks
        const bufferSize = SAMPLE_RATE * CHUNK_DURATION;
        const processor = audioContext.createScriptProcessor(2048, 1, 1);
        
        // Connect nodes
        source.connect(analyser);
        analyser.connect(processor);
        processor.connect(audioContext.destination);
        
        // Handle audio processing
        processor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          handleAudioProcess(inputData);
        };

        console.log('Audio recording initialized successfully');
      } catch (error) {
        console.error('Error initializing audio recording:', error);
        onAudioData(new Float32Array([0])); // Send empty data to trigger status update
      }
    };

    if (isListening) {
      initializeRecording();
    } else {
      // When stopped, update the message
      onAudioData(new Float32Array([0])); // Send empty data to reset status
      // Reset buffer
      audioBufferRef.current = new Float32Array(0);
    }

    // Cleanup
    return () => {
      if (analyserRef.current) {
        analyserRef.current.disconnect();
      }
      if (sourceRef.current) {
        sourceRef.current.disconnect();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      // Reset buffer
      audioBufferRef.current = new Float32Array(0);
    };
  }, [isListening, onAudioData]);

  const handleAudioProcess = async (inputData: Float32Array) => {
    try {
      // Append new audio data to buffer
      const newBuffer = new Float32Array(audioBufferRef.current.length + inputData.length);
      newBuffer.set(audioBufferRef.current);
      newBuffer.set(inputData, audioBufferRef.current.length);
      audioBufferRef.current = newBuffer;

      // If we have enough data for a chunk
      const chunkSize = SAMPLE_RATE * CHUNK_DURATION;
      const overlapSize = SAMPLE_RATE * OVERLAP_DURATION;

      if (audioBufferRef.current.length >= chunkSize) {
        // Get the chunk with overlap
        const chunkWithOverlap = audioBufferRef.current.slice(0, chunkSize);
        
        // Keep the overlapping portion for the next chunk
        audioBufferRef.current = audioBufferRef.current.slice(chunkSize - overlapSize);

        // Send the chunk to the backend
        console.log('Sending audio chunk to:', `${API_BASE}/audio`);
        
        const response = await fetch(`${API_BASE}/audio`, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          mode: 'cors',
          body: JSON.stringify({
            audio: Array.from(chunkWithOverlap)
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Server response:', errorText);
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Audio chunk processed successfully');
        onAudioData(data);
      }
    } catch (error) {
      console.error('Audio processing error:', {
        message: error instanceof Error ? error.message : String(error),
        url: API_BASE,
        timestamp: new Date().toISOString()
      });
    }
  };

  return null;
};