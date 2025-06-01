# Multi-Sport Action Tracker - Quick Start Guide

## 💻 Project Setup

### Backend Setup (Python FastAPI Server)

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Backend Server**:
   ```bash
   python backend/main.py
   ```
   The server will start at http://localhost:8000

3. **Test WebSocket Connection**:
   Open `websocket_test.html` to verify WebSocket connections are working properly.

### Frontend Setup (React.js)

1. **Install Node.js Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start Frontend Development Server**:
   ```bash
   cd frontend
   npm start
   ```
   The React app will start at http://localhost:3000

## 🚀 Using the Application

1. **Access the Dashboard**: Open http://localhost:3000 in your web browser

2. **Create a New Session**:
   - Click "New Session" in the sidebar
   - Select a sport (Basketball, Tennis, Golf, Soccer)
   - Configure tracking settings
   - Start tracking

3. **Real-time Tracking**:
   - Stand in front of your camera
   - Perform sport-specific actions
   - Receive real-time feedback on your form and technique

4. **View Analytics**:
   - See your performance metrics and improvements
   - Review session history and statistics

## 🛠️ Troubleshooting

### WebSocket Connection Issues

If you experience WebSocket connection errors:

1. **Check CORS Settings**:
   - Ensure your browser allows WebSocket connections to localhost
   - Verify CORS settings in `backend/main.py`

2. **Test Simple WebSocket**:
   - Use the included `websocket_test.html` page
   - Connect to `ws://localhost:8000/ws` or `ws://localhost:8000/ws/test`

3. **Check Backend Logs**:
   - Monitor the terminal where your backend is running
   - Look for connection rejection messages

### Camera Access Issues

If the application cannot access your camera:

1. **Check Browser Permissions**:
   - Allow camera access when prompted
   - Verify camera permissions in your browser settings

2. **Verify Camera Configuration**:
   - Check camera settings in the `.env` file
   - Ensure your camera is not being used by another application

## 📊 Development Tools

- **VS Code Tasks**:
  - `Start Backend Server`: Runs the Python FastAPI server
  - `Install Frontend Dependencies`: Installs React dependencies
  - `Start Frontend`: Starts the React development server

- **Test Script**:
  ```bash
  python test_project.py
  ```
  Runs comprehensive tests for all components

## 📝 Contributing

1. Create a new branch for your feature
2. Make your changes and test them
3. Submit a pull request with a clear description

## 📚 More Information

For additional documentation, code structure details, and API references, see the full project documentation.
