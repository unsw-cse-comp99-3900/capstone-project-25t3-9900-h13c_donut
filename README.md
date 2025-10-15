# Fast Accent Translator

Real-time bilingual accent translator with speech-to-text (ASR) and text-to-speech (TTS) capabilities.

## Tech Stack

**Backend:**
- FastAPI (Python)
- WebSocket
- BE-5 ASR (Whisper)
- ElevenLabs TTS
- JWT Authentication

**Frontend:**
- React
- Vite
- WebSocket Client

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 20+
- ElevenLabs API Key
- OpenAI API Key (for ASR)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys

# Start ASR service (Terminal 1)
cd asr
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Start main server (Terminal 2)
cd ..
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 3. Access Application

Open browser: `http://localhost:5173`

Default credentials: Check `frontend/src/api/mockDB.js`

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── websocket/       # WebSocket handlers
│   │   ├── services/        # ASR & TTS services
│   │   ├── models/          # Data models
│   │   └── auth/            # Authentication
│   ├── asr/                 # ASR module
│   ├── tts/                 # TTS module
│   └── main.py              # FastAPI entry point
│
└── frontend/
    ├── src/
    │   ├── api/             # API clients
    │   ├── pages/           # React pages
    │   └── main.jsx         # App entry point
    └── package.json

```

## Environment Variables

### Backend (.env)

```env
# API Keys
ELEVENLABS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# JWT
JWT_SECRET_KEY=your-secret-key

# Services
ASR_SERVICE_URL=http://localhost:8001
```

### Frontend (.env)

```env
VITE_API_BASE=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws/realtime
```

## WebSocket Protocol

### Client → Server

```json
// Initialize session
{"type": "init", "accent": "us", "model": "free"}

// Send audio chunk
{"type": "audio", "data": "base64_audio", "sequence": 0}

// Stop recording
{"type": "stop"}
```

### Server → Client

```json
// Partial transcript
{"type": "partial", "text": "Hello", "sequence": 0}

// Final transcript
{"type": "final", "text": "Hello world"}

// TTS audio chunk
{"type": "tts_chunk", "bytes_b64": "base64_audio", "seq": 0, "isLast": false}

// Processing complete
{"type": "done", "sessionId": "..."}
```

