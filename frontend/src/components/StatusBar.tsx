import React from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';

const blink = keyframes`
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
`;

const StatusContainer = styled.div`
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 25px;
  padding: 0.8rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  z-index: 20;
  transition: all 0.6s ease;

  body.light-mode & {
    background: rgba(255, 255, 255, 0.8);
    border-color: rgba(0, 0, 0, 0.1);
    color: #1d1d1f;
  }
`;

const StatusDot = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #FF3B30;
  animation: ${blink} 2s infinite;

  &.connected {
    background: #32D74B;
    animation: none;
  }
`;

interface StatusBarProps {
  isConnected: boolean;
  statusText: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({ isConnected, statusText }) => (
  <StatusContainer>
    <StatusDot className={isConnected ? 'connected' : ''} />
    <span>{statusText}</span>
  </StatusContainer>
);