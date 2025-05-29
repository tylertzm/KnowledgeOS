import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { SiriOrb } from './components/SiriOrb';
import { StatusBar } from './components/StatusBar';
import { ThemeToggle } from './components/ThemeToggle';
import { GlobalStyles } from './styles/GlobalStyles';
import { StatusResponse } from './types';
import { AudioRecorder } from './components/AudioRecorder';
import { InfoIcon } from './components/InfoIcon';
import { v4 as uuidv4 } from 'uuid';

const AppWrapper = styled.div`
  height: 100vh;
  overflow: hidden;
  position: relative;
`;

const BackgroundGlow = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 800px;
  height: 800px;
  background: radial-gradient(circle, rgba(0, 122, 255, 0.15) 0%, rgba(0, 122, 255, 0.05) 30%, transparent 70%);
  border-radius: 50%;
  z-index: 1;
  animation: ambient-pulse 4s ease-in-out infinite;
  transition: all 0.6s ease;

  body.light-mode & {
    background: radial-gradient(circle, rgba(0, 122, 255, 0.08) 0%, rgba(0, 122, 255, 0.03) 30%, transparent 70%);
  }
`;

const Container = styled.div`
  position: relative;
  z-index: 10;
  text-align: center;
  max-width: 600px;
  width: 90%;
  margin: 0 auto;
  padding-top: 100px;
`;

const TextDisplay = styled.div`
  padding: 2rem;
  margin: 2rem 0;
  height: 300px;
  max-height: 40vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(12px);
  
  /* Custom Scrollbar Styling */
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
  
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    border: 2px solid transparent;
    background-clip: content-box;
    transition: all 0.3s ease;
  }

  &::-webkit-scrollbar-thumb:hover {
    background-color: rgba(255, 255, 255, 0.5);
  }

  &::-webkit-scrollbar-corner {
    background: transparent;
  }

  /* Light mode styles */
  body.light-mode & {
    background: rgba(255, 255, 255, 0.8);
    scrollbar-color: rgba(0, 0, 0, 0.2) transparent;

    &::-webkit-scrollbar-thumb {
      background-color: rgba(0, 0, 0, 0.2);
      border: 2px solid transparent;
      background-clip: content-box;
    }

    &::-webkit-scrollbar-thumb:hover {
      background-color: rgba(0, 0, 0, 0.3);
    }
  }

  @media (max-width: 768px) {
    padding: 1.5rem;
    margin: 1rem 0;
    height: 250px;
  }
`;

const ModeIndicator = styled.div`
  font-size: 0.9rem;
  font-weight: 500;
  color: #007AFF;
  margin-bottom: 1rem;
  letter-spacing: 1px;
  text-transform: uppercase;
`;

const Transcription = styled.div<{ isEmpty: boolean }>`
  font-size: 1.3rem;
  font-weight: 400;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  color: rgba(255, 255, 255, 0.9);
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.6s ease;
  animation: ${props => props.isEmpty ? 'loading-fade 1.5s ease-in-out infinite' : 'none'};

  body.light-mode & {
    color: rgba(29, 29, 31, 0.9);
  }

  @media (max-width: 768px) {
    font-size: 1.1rem;
  }
`;

const Response = styled.div<{ mode: string }>`
  font-size: 1.1rem;
  font-weight: 300;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  margin-top: 1rem;
  margin-bottom: 1rem;
  max-width: 100%;
  width: 100%;
  word-wrap: break-word;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);

  body.light-mode & {
    color: rgba(29, 29, 31, 0.8);
    border-top-color: rgba(0, 0, 0, 0.1);
    background: rgba(0, 0, 0, 0.03);
  }

  @media (max-width: 768px) {
    font-size: 1rem;
    padding: 1rem;
    margin-top: 0.5rem;
  }
`;

const API_BASE = process.env.REACT_APP_API_URL || 'https://knowledgeos.onrender.com';

console.log('Environment:', process.env.NODE_ENV);
console.log('Using API URL:', API_BASE);

export const App: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [status, setStatus] = useState<StatusResponse>({
    mode: 'Transcription',
    transcription: 'Tap globe to start recording...',
    response: ''
  });
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [hasMicPermission, setHasMicPermission] = useState<boolean>(false);
  const [sessionId] = useState(() => {
    // Generate or retrieve a unique session ID
    const existingSessionId = localStorage.getItem('sessionId');
    if (existingSessionId) return existingSessionId;
    const newSessionId = uuidv4();
    localStorage.setItem('sessionId', newSessionId);
    return newSessionId;
  });

  // Set initial theme class on mount
  useEffect(() => {
    document.body.classList.toggle('light-mode', !isDarkMode);
  }, [isDarkMode]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const apiUrl = new URL('/status', API_BASE).toString();
        const response = await fetch(apiUrl, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': window.location.origin,
            'Session-Id': sessionId, // Include session ID in headers
          },
          mode: 'cors',
          cache: 'no-cache',
        });
        
        if (!response.ok) {
          const text = await response.text();
          console.error('Response content:', text);
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Backend response:', data);
        setStatus(data);
        setIsConnected(true);
        
      } catch (error) {
        console.error('Connection details:', {
          url: API_BASE,
          error: error instanceof Error ? error.message : String(error)
        });
        setIsConnected(false);
        setStatus(prev => ({ ...prev, mode: 'OFFLINE' }));
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const requestMicrophoneAccess = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        setStatus(prev => ({
          ...prev,
          transcription: 'Tap globe to start recording'
        }));
      } catch (error) {
        console.error('Microphone access denied:', error);
        setStatus(prev => ({
          ...prev,
          transcription: 'Please enable microphone access'
        }));
      }
    };

    requestMicrophoneAccess();
  }, []);

  const modeOptions = ['Transcription', 'AI', 'WebSearch'];

  const switchMode = (newMode: string) => {
    setStatus(prev => ({
      ...prev,
      mode: newMode as StatusResponse['mode'],
      transcription: `Switched to ${newMode} mode`,
      response: ''
    }));
  };

  useEffect(() => {
    if (status.transcription) {
      const lowerCaseTranscription = status.transcription.toLowerCase();
      if (lowerCaseTranscription.includes('transcription mode')) {
        switchMode('Transcription');
      } else if (lowerCaseTranscription.includes('ai mode')) {
        switchMode('AI');
      } else if (lowerCaseTranscription.includes('web search mode')) {
        switchMode('WebSearch');
      }
    }
  }, [status.transcription]);

  // Reset mode to "Transcription" on page reload
  useEffect(() => {
    setStatus(prev => ({ ...prev, mode: 'Transcription' }));
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(prev => !prev);
  };

  const handleAudioData = async (audioData: Float32Array) => {
    try {
      const response = await fetch(`${API_BASE}/audio`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Origin': window.location.origin,
          'Session-Id': sessionId, // Include session ID in headers
        },
        mode: 'cors',
        cache: 'no-cache',
        body: JSON.stringify({
          audio: Array.from(audioData),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.transcription) {
        setStatus(prev => ({
          ...prev,
          transcription: data.transcription,
          response: data.response || prev.response
        }));
      }
    } catch (error) {
      console.error('Error sending audio data:', error);
    }
  };

  useEffect(() => {
    const startRecording = async () => {
      if (!hasMicPermission) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          stream.getTracks().forEach(track => track.stop());
          setHasMicPermission(true);
          setIsRecording(true); // Automatically start recording
        } catch (error) {
          console.error('Microphone access denied:', error);
          setStatus(prev => ({
            ...prev,
            transcription: 'Please enable microphone access'
          }));
        }
      } else {
        setIsRecording(true); // Automatically start recording if permission is already granted
      }
    };

    startRecording();
  }, [hasMicPermission]);

  const toggleRecording = () => {
    setIsRecording(prev => !prev); // Toggle recording state when the globe is tapped
  };

  return (
    <>
      <GlobalStyles />
      <AppWrapper>
        <BackgroundGlow />
        <InfoIcon />
        <StatusBar 
          isConnected={isConnected} 
          statusText={isConnected ? 'Neural Link Active' : 'Connection Lost'} 
        />
        <ThemeToggle isDark={isDarkMode} onToggle={toggleTheme} />
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <label 
            htmlFor="mode-select" 
            style={{
              marginRight: '10px',
              fontSize: '1rem',
              fontWeight: 'bold',
              color: '#007AFF',
              textTransform: 'uppercase',
              letterSpacing: '1px',
            }}
          >
            Select Mode:
          </label>
          <select
            id="mode-select"
            value={status.mode}
            onChange={(e) => switchMode(e.target.value)}
            style={{
              padding: '0.5rem',
              borderRadius: '8px',
              border: '1px solid #ccc',
              fontSize: '1rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            {modeOptions.map(mode => (
              <option key={mode} value={mode}>{mode}</option>
            ))}
          </select>
        </div>
        <Container>
          <SiriOrb 
            isListening={isRecording} 
            onClick={toggleRecording} // Tap to stop or start recording
          />
          <AudioRecorder
            isListening={isRecording}
            onAudioData={handleAudioData}
          />
          <TextDisplay>
            <ModeIndicator>
              {status.mode === 'Transcription' ? 'Multilingual Transcription' : status.mode}
            </ModeIndicator>
            <Transcription isEmpty={!status.transcription}>
              {status.transcription || 'Listening for your voice...'}
            </Transcription>
            {status.response && ['AI', 'WebSearch'].includes(status.mode) && (
              <Response mode={status.mode.toLowerCase()}>
                {status.response}
              </Response>
            )}
            <h5 style={{ textAlign: 'center' }}>tap the globe to stop recording</h5>
            <h5 style={{ textAlign: 'center' }}>to switch modes, ask politely!</h5>
            <h5 style={{ textAlign: 'center' }}>average latency is 4s</h5>
            <h5 style={{ textAlign: 'center' }}>it might take up to a minute to connect!</h5>
          </TextDisplay>

        </Container>
      </AppWrapper>
    </>
  );
};
