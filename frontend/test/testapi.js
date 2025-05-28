<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Siri-Style Interface</title>
    <style>
      body {
        background: #0c0c0c;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      }

      h1 {
        font-size: 1.5rem;
        margin-bottom: 2rem;
      }

      .pulse {
        width: 100px;
        height: 100px;
        background: radial-gradient(circle at center, #4fc3f7, #0288d1);
        border-radius: 50%;
        animation: pulse-animation 1.5s infinite ease-in-out;
        box-shadow: 0 0 30px rgba(0, 150, 255, 0.6);
      }

      @keyframes pulse-animation {
        0% {
          transform: scale(1);
          opacity: 1;
        }
        50% {
          transform: scale(1.2);
          opacity: 0.7;
        }
        100% {
          transform: scale(1);
          opacity: 1;
        }
      }

      #info {
        margin-top: 2rem;
        font-size: 1rem;
        color: #ccc;
        max-width: 80vw;
        text-align: center;
        white-space: pre-wrap;
      }

      .status {
        color: #4fc3f7;
        font-size: 0.9rem;
        margin-top: 1rem;
      }
    </style>
  </head>
  <body>
    <h1>🎙️ Listening...</h1>
    <div class="pulse"></div>
    <p id="info">Speak now...</p>
    <div id="status" class="status">Connecting...</div>

    <script>
      const apiUrl = 'http://192.168.0.150:5001/status';
      const statusElement = document.getElementById('status');
      const infoElement = document.getElementById('info');
      
      let isConnected = false;

      async function fetchStatus() {
        try {
          statusElement.textContent = 'Fetching...';
          
          const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
            // Add no-cors mode if CORS is still an issue (but this limits what you can read)
            // mode: 'no-cors'
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          
          const data = await response.json();

          // Build display string
          let displayText = `Mode: ${data.mode}\n`;
          displayText += `Transcription: ${data.transcription || "(none)"}\n`;
          if (data.mode === "AI" && data.response) {
            displayText += `Response: ${data.response}`;
          }

          // Update info paragraph
          infoElement.textContent = displayText;
          statusElement.textContent = 'Connected ✓';
          statusElement.style.color = '#4caf50';
          
          isConnected = true;
          console.log('Status data:', data);
          
        } catch (error) {
          console.error('Fetch error:', error);
          infoElement.textContent = 'Error connecting to API';
          statusElement.textContent = `Error: ${error.message}`;
          statusElement.style.color = '#f44336';
          isConnected = false;
        }
      }

      // Initial fetch
      fetchStatus();
      
      // Poll every 2 seconds
      setInterval(fetchStatus, 2000);
    </script>
  </body>
</html>