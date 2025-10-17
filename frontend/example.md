# 1. Directory structure

## backend/
├── app/
│   ├── core/                 # Core functionality modules
│   │   ├── __init__.py
│   │   └── pubsub.py         # Pub/Sub message queue handling
│   ├── routers/              # WebSocket routes
│   │   ├── __init__.py
│   │   ├── ws_text.py        
│   │   ├── ws_tts.py         
│   │   └── ws_upload.py      
│   └── services/                 # Business service layer
│       ├── __init__.py
│       ├── asr_openai.py         
│       └──tts_elevenlabs.py     
├── __init__.py
├── config.py                 # Configuration file
└── main.py                   # FastAPI application entry point

   
## frontend/
├── src/
│   ├── api/                   # API service modules
│   │   ├── auth.js
│   │   ├── conversations.js
│   │   ├── dashboard.js
│   │   ├── streamClient.js
│   ├── assets/                # Static resources (images, fonts, etc.)
│   ├── components/            # Reusable UI components
│   ├── pages/                 # Page-level components
│   │   ├── Dashboard/
│   │   ├── ForgotPassword/
│   │   ├── Login/
│   │   └── Register/
│   ├── App.css               # Main application styles
│   ├── App.jsx               # Root application component
│   ├── index.css             # Global styles
│   └── main.jsx              # Application entry point
└── public/                    # Static assets

# 2. How to Run?
## If you do not have the FFmpeg, please run these commands in order to install:
winget search ffmpeg
winget install -e --id Gyan.FFmpeg
ffmpeg -version

## /Backend: cd the directory to /Backend, and run the following commands.
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Go to the link http://localhost:8000/health to check, if it succeeds, you will see {"ok":true}.

## /Frontend: cd the directory to /Frontend, and run the following commands.
npm install
npm run dev

Go to the link http://localhost:5173 to check, if it succeeds, you will see the `login` page.
When you first use the system, you should `Register` first.