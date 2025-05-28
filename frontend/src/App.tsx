import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { SiriOrb } from './components/SiriOrb';
import { StatusBar } from './components/StatusBar';
import { ThemeToggle } from './components/ThemeToggle';
import { GlobalStyles } from './styles/GlobalStyles';
import { StatusResponse } from './types';

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
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;

  @media (max-width: 768px) {
    padding: 1.5rem;
    margin: 1rem 0;
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
  padding-top: 1.5rem;
  margin-top: 1rem;
  transition: all 0.6s ease;

  body.light-mode & {
    color: rgba(29, 29, 31, 0.8);
    border-top-color: rgba(0, 0, 0, 0.1);
  }

  @media (max-width: 768px) {
    font-size: 1rem;
  }
`;

export const App: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [status, setStatus] = useState<StatusResponse>({
    mode: 'OFFLINE',
    transcription: 'Establishing neural connection...',
    response: ''
  });
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://192.168.0.150:5001/status');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        setStatus(data);
        setIsConnected(true);
      } catch (error) {
        console.error('Connection error:', error);
        setIsConnected(false);
        setStatus(prev => ({ ...prev, mode: 'OFFLINE' }));
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => setIsDarkMode(!isDarkMode);

  return (
    <>
      <GlobalStyles />
      <AppWrapper className={isDarkMode ? '' : 'light-mode'}>
        <BackgroundGlow />
        <StatusBar 
          isConnected={isConnected} 
          statusText={isConnected ? 'Neural Link Active' : 'Connection Lost'} 
        />
        <ThemeToggle isDark={isDarkMode} onToggle={toggleTheme} />
        
        <Container>
          <SiriOrb 
            isListening={['AI', 'WebSearch'].includes(status.mode)} 
            onClick={toggleTheme}
          />
          <TextDisplay>
            <ModeIndicator>{status.mode}</ModeIndicator>
            <Transcription isEmpty={!status.transcription}>
              {status.transcription || 'Listening for your voice...'}
            </Transcription>
            {status.response && ['AI', 'WebSearch'].includes(status.mode) && (
              <Response mode={status.mode.toLowerCase()}>
                {status.response}
              </Response>
            )}
          </TextDisplay>
        </Container>
      </AppWrapper>
    </>
  );
};
