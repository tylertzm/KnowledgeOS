import React from 'react';
import styled from '@emotion/styled';

const ToggleButton = styled.div`
  position: absolute;
  top: 30px;
  right: 30px;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.3s ease;
  z-index: 20;

  body.light-mode & {
    background: rgba(255, 255, 255, 0.8);
    border-color: rgba(0, 0, 0, 0.1);
    color: #1d1d1f;
  }

  &:hover {
    transform: scale(1.1);
    background: rgba(0, 0, 0, 0.6);
  }

  body.light-mode &:hover {
    background: rgba(255, 255, 255, 0.95);
  }

  @media (max-width: 768px) {
    right: 20px;
    top: 20px;
    width: 45px;
    height: 45px;
  }
`;

interface ThemeToggleProps {
  isDark: boolean;
  onToggle: () => void;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ isDark, onToggle }) => (
  <ToggleButton onClick={onToggle}>
    {isDark ? '🌙' : '☀️'}
  </ToggleButton>
);
