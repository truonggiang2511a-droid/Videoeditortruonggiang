import React from 'react';
import { createRoot } from 'react-dom/client';
import SaaSApp from './SaaSApp.jsx';
import './styles.css';
import './os.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <SaaSApp />
  </React.StrictMode>,
);
