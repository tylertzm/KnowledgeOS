import React, { useEffect, useRef, useState } from 'react';

interface AudioRecorderProps {
  isListening: boolean;
  onAudioData: (audioData: Float32Array) => void;
}

const API_BASE = process.env.REACT_APP_API_URL || 'https://knowledgeos.onrender.com';
const CHUNK_DURATION = 4000; // 4 seconds in milliseconds
const OVERLAP_DURATION = 2000; // 2 seconds in milliseconds

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ isListening, onAudioData }) => {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    const initializeRecording = async () => {
      try {
        // Request microphone access with specific constraints for better quality
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            channelCount: 1,
            sampleRate: 16000
          }
        });

        streamRef.current = stream;
        console.log('Got media stream');

        // Create MediaRecorder with audio/webm MIME type which is widely supported
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: MediaRecorder.isTypeSupported('audio/webm') 
            ? 'audio/webm' 
            : 'audio/ogg'
        });

        mediaRecorderRef.current = mediaRecorder;
        chunksRef.current = [];

        // Handle data available event
        mediaRecorder.ondataavailable = async (event) => {
          if (event.data.size > 0) {
            chunksRef.current.push(event.data);
            
            // Convert blob to Float32Array
            const arrayBuffer = await event.data.arrayBuffer();
            const audioContext = new AudioContext();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            const channelData = audioBuffer.getChannelData(0);
            
            // Send the audio data
            onAudioData(channelData);
          }
        };

        // Start recording with timeslice for continuous data
        mediaRecorder.start(CHUNK_DURATION - OVERLAP_DURATION);
        setIsRecording(true);
        console.log('Recording started');

      } catch (error) {
        console.error('Error initializing recording:', error);
      }
    };

    const stopRecording = () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      chunksRef.current = [];
      console.log('Recording stopped');
    };

    if (isListening && !isRecording) {
      initializeRecording();
    } else if (!isListening && isRecording) {
      stopRecording();
    }

    return () => {
      stopRecording();
    };
  }, [isListening, onAudioData]);

  return null;
};