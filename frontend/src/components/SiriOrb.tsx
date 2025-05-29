import React from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';

const orbRotate = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const pulse = keyframes`
  0% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); opacity: 0.8; }
`;

const listeningGlow = keyframes`
  0%, 100% { box-shadow: 0 0 60px rgba(255, 255, 255, 0.1), inset 0 0 60px rgba(255, 255, 255, 0.05); }
  50% { box-shadow: 0 0 100px rgba(255, 255, 255, 0.2), inset 0 0 80px rgba(255, 255, 255, 0.1); }
`;

const listeningGlowLight = keyframes`
  0%, 100% { 
    box-shadow: 
      0 0 60px rgba(0, 0, 0, 0.08),
      inset 0 0 60px rgba(0, 0, 0, 0.02),
      0 8px 32px rgba(0, 0, 0, 0.12);
  }
  50% { 
    box-shadow: 
      0 0 80px rgba(0, 122, 255, 0.15),
      inset 0 0 80px rgba(0, 122, 255, 0.05),
      0 12px 40px rgba(0, 122, 255, 0.2);
  }
`;

const OrbContainer = styled.div`
  position: relative;
  width: 280px;
  height: 280px;
  margin: 0 auto 3rem;
  cursor: pointer;
  transition: transform 0.2s ease;

  &:hover {
    transform: scale(1.02);
  }

  @media (max-width: 768px) {
    width: 220px;
    height: 220px;
    margin-bottom: 2rem;
  }
`;

const OrbOuter = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.1);
  background: transparent;
  animation: ${orbRotate} 8s linear infinite;
  transition: border-color 0.6s ease;

  body.light-mode & {
    border-color: rgba(0, 0, 0, 0.08);
  }
`;

const OrbMiddle = styled.div`
  position: absolute;
  top: 15px;
  left: 15px;
  width: calc(100% - 30px);
  height: calc(100% - 30px);
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: transparent;
  animation: ${orbRotate} 6s linear infinite reverse;
  transition: border-color 0.6s ease;

  body.light-mode & {
    border-color: rgba(0, 0, 0, 0.04);
  }
`;

const OrbInner = styled.div`
  position: absolute;
  top: 30px;
  left: 30px;
  width: calc(100% - 60px);
  height: calc(100% - 60px);
  border-radius: 50%;
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
  animation: ${pulse} 2s ease-in-out infinite;
  box-shadow: 
    0 0 60px rgba(255, 255, 255, 0.1),
    inset 0 0 60px rgba(255, 255, 255, 0.05);
  transition: all 0.6s ease;

  .light-mode & {
    background: linear-gradient(135deg, #ffffff 0%, #f5f5f7 50%, #ffffff 100%);
    box-shadow: 
      0 0 60px rgba(0, 0, 0, 0.08),
      inset 0 0 60px rgba(0, 0, 0, 0.02),
      0 8px 32px rgba(0, 0, 0, 0.12);
  }

  .listening & {
    animation: ${pulse} 0.8s ease-in-out infinite, ${listeningGlow} 2s ease-in-out infinite;
  }

  .light-mode .listening & {
    animation: ${pulse} 0.8s ease-in-out infinite, ${listeningGlowLight} 2s ease-in-out infinite;
  }
`;

interface SiriOrbProps {
  isListening: boolean;
  onClick: () => void;
}

export const SiriOrb: React.FC<SiriOrbProps> = ({ isListening, onClick }) => (
  <OrbContainer onClick={onClick} className={isListening ? 'listening' : ''}>
    <OrbOuter />
    <OrbMiddle />
    <OrbInner />
  </OrbContainer>
);
