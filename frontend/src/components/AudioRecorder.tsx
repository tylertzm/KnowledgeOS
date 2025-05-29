import React, { useEffect, useRef } from 'react';

interface AudioRecorderProps {
  isListening: boolean;
  onAudioData: (audioData: Float32Array) => void;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ isListening, onAudioData }) => {
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    const initializeRecording = async () => {
      try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        });
        
        streamRef.current = stream;
        
        // Create audio context
        const audioContext = new AudioContext();
        audioContextRef.current = audioContext;
        
        // Create source
        const source = audioContext.createMediaStreamSource(stream);
        sourceRef.current = source;
        
        // Create processor
        const processor = audioContext.createScriptProcessor(2048, 1, 1);
        processorRef.current = processor;
        
        // Connect nodes
        source.connect(processor);
        processor.connect(audioContext.destination);
        
        // Handle audio processing
        processor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          onAudioData(inputData);
        };

        console.log('Audio recording initialized successfully');
      } catch (error) {
        console.error('Error initializing audio recording:', error);
      }
    };

    if (isListening) {
      initializeRecording();
    }

    // Cleanup
    return () => {
      if (processorRef.current) {
        processorRef.current.disconnect();
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
    };
  }, [isListening, onAudioData]);

  return null;
};