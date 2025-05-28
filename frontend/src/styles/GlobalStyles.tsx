import { Global, css } from '@emotion/react';

export const GlobalStyles = () => (
  <Global
    styles={css`
      @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&display=swap');
      
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }

      body {
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 50%, #2d2d2d 100%);
        color: white;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      }

      body.light-mode {
        background: linear-gradient(135deg, #f5f5f7 0%, #ffffff 50%, #fafafa 100%);
        color: #1d1d1f;
      }

      @keyframes ambient-pulse {
        0%, 100% { 
          transform: translate(-50%, -50%) scale(1); 
          opacity: 0.6; 
        }
        50% { 
          transform: translate(-50%, -50%) scale(1.1); 
          opacity: 0.8; 
        }
      }

      @keyframes loading-fade {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
    `}
  />
);