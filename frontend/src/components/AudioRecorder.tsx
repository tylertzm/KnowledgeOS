import React, { useEffect, useRef } from 'react';

interface AudioRecorderProps {
  isListening: boolean;
  onAudioData: (audioData: Float32Array) => void;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ isListening, onAudioData }) => {
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const bufferRef = useRef<Float32Array[]>([]);
  const lastSentRef = useRef<number>(0);
  const BUFFER_SIZE = 2048;  // Audio processing buffer size
  const SEND_INTERVAL = 2000;  // Send every 2 seconds

  useEffect(() => {
    const initAudio = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        
        const audioContext = new AudioContext();
        audioContextRef.current = audioContext;
        
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(BUFFER_SIZE, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
          const inputData = e.inputBuffer.getChannelData(0);
          bufferRef.current.push(new Float32Array(inputData));

          const now = Date.now();
          if (now - lastSentRef.current >= SEND_INTERVAL) {
            // Concatenate all buffers
            const totalLength = bufferRef.current.reduce((acc, curr) => acc + curr.length, 0);
            const concatenated = new Float32Array(totalLength);
            let offset = 0;
            
            bufferRef.current.forEach(buffer => {
              concatenated.set(buffer, offset);
              offset += buffer.length;
            });

            onAudioData(concatenated);
            bufferRef.current = [];
            lastSentRef.current = now;
          }
        };
      } catch (error) {
        console.error('Error accessing microphone:', error);
      }
    };

    if (isListening) {
      initAudio();
    }

    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      bufferRef.current = [];
    };
  }, [isListening, onAudioData]);

  return null;
};