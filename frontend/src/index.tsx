import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { GlobalStyles } from './styles/GlobalStyles';
import { Analytics } from '@vercel/analytics/react'; // Correct import for React


const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <GlobalStyles />
    <Analytics />
    <App />
  </React.StrictMode>
);
