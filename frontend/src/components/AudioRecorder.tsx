import React, { useEffect, useRef } from 'react';

interface AudioRecorderProps {
  isListening: boolean;
  onAudioData: (audioData: Float32Array) => void;
}

const API_BASE = process.env.REACT_APP_API_URL || 'https://knowledgeos.onrender.com';

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
        console.log('Recording started - speak now');
        
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

  const handleAudioProcess = async (inputData: Float32Array) => {
    try {
      console.log('Sending audio data to:', `${API_BASE}/audio`);
      
      // First check if endpoint is available
      const checkResponse = await fetch(`${API_BASE}/audio`, {
        method: 'OPTIONS',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        mode: 'cors'
      });

      if (!checkResponse.ok) {
        throw new Error(`CORS check failed: ${checkResponse.status}`);
      }

      // Send actual audio data
      const response = await fetch(`${API_BASE}/audio`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        mode: 'cors',
        body: JSON.stringify({
          audio: Array.from(inputData)
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Audio data processed successfully');
      onAudioData(data);
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