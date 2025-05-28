#!/bin/bash

echo "🚀 Starting KnowledgeOS setup and launch..."

# Check if Python virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi
# Activate virtual environment and install Python requirements
echo "📥 Installing Python dependencies..."
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# Install Node.js dependencies
echo "📥 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Start backend server in background
echo "🌐 Starting backend server..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to initialize (adjust sleep time if needed)
sleep 3

# Start frontend
echo "🖥 Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!

# Handle script termination
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Keep script running
wait
