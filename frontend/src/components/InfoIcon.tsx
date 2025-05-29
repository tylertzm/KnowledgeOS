import React, { useState } from 'react';
import styled from '@emotion/styled';

const InfoContainer = styled.div`
  position: absolute;
  top: 30px;
  left: 30px;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 15px;

  @media (max-width: 768px) {
    top: 20px;
    left: 20px;
  }
`;

const LatencyMessage = styled.span`
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;

  body.light-mode & {
    color: rgba(0, 0, 0, 0.6);
  }
`;

const InfoButton = styled.div`
  width: 50px;
  height: 50px;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.5rem;
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.1);
    background: rgba(0, 0, 0, 0.6);
  }

  body.light-mode & {
    background: rgba(255, 255, 255, 0.8);
    border-color: rgba(0, 0, 0, 0.1);
    color: #1d1d1f;

    &:hover {
      background: rgba(255, 255, 255, 0.95);
    }
  }

  @media (max-width: 768px) {
    width: 45px;
    height: 45px;
  }
`;

const InfoPanel = styled.div<{ isVisible: boolean }>`
  position: absolute;
  top: 70px;
  left: 0;
  width: 300px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px;
  color: white;
  font-size: 0.95rem;
  line-height: 1.6;
  opacity: ${props => props.isVisible ? 1 : 0};
  visibility: ${props => props.isVisible ? 'visible' : 'hidden'};
  transform: translateY(${props => props.isVisible ? '0' : '-10px'});
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);

  body.light-mode & {
    background: rgba(255, 255, 255, 0.95);
    color: #1d1d1f;
    border-color: rgba(0, 0, 0, 0.1);
  }

  h3 {
    margin: 0 0 10px;
    color: #007AFF;
    font-size: 1rem;
  }

  p {
    margin: 0 0 15px;
    &:last-child {
      margin-bottom: 0;
    }
  }

  @media (max-width: 768px) {
    width: 280px;
    font-size: 0.9rem;
  }
`;

export const InfoIcon: React.FC = () => {
  const [showInfo, setShowInfo] = useState(false);

  return (
    <InfoContainer>
      <InfoButton onClick={() => setShowInfo(!showInfo)}>ⓘ</InfoButton>
      <LatencyMessage>(average latency is 4 seconds, so be patient!)</LatencyMessage>
      <InfoPanel isVisible={showInfo}>
        <h3>Available Modes</h3>
        <p><strong>Transcription Mode:</strong> Simply converts your speech to text. Default mode when you start.</p>
        <p><strong>AI Mode:</strong> Say "AI mode" to activate. Your speech will be processed by an AI assistant that can answer questions and help with tasks.</p>
        <p><strong>Web Search Mode:</strong> Say "web search mode" to activate. Searches the web for answers to your questions.</p>
        <p>Tap the glowing orb to start/stop recording.</p>
      </InfoPanel>
    </InfoContainer>
  );
};
