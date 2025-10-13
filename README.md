# 1. Directory structure

## backend/
├── app/
│   ├── core/                 # Core functionality modules
│   │   ├── __init__.py
│   │   └── pubsub.py         # Pub/Sub message queue handling
│   └── routers/              # WebSocket routes
│       ├── __init__.py
│       ├── ws_text.py        # Text processing WebSocket
│       ├── ws_tts.py         # Text-to-speech WebSocket
│       └── ws_upload.py      # File upload WebSocket
├── services/                 # Business service layer
│   ├── __init__.py
│   ├── asr_openai.py         # OpenAI speech recognition service
│   └── tts_elevenlabs.py     # ElevenLabs text-to-speech service
├── __init__.py
├── config.py                 # Configuration file
├── main.py                   # FastAPI application entry point
├── .env                      # Environment variables (local)
├── .env.example              # Environment variables template
├── .gitignore
└── requirements.txt          # Python dependencies
   
## frontend/
├── node_modules/              # npm dependencies
├── public/                    # Static assets
├── src/
│   ├── api/                   # API service modules
│   ├── assets/                # Static resources (images, fonts, etc.)
│   ├── components/            # Reusable UI components
│   ├── pages/                 # Page-level components
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.jsx
│   │   │   └── Dashboard.module.css
│   │   ├── ForgotPassword/
│   │   │   ├── ForgotPasswordPage.jsx
│   │   │   └── ForgotPasswordPage.module.css
│   │   ├── Login/
│   │   │   ├── LoginPage.jsx
│   │   │   └── LoginPage.module.css
│   │   └── Register/
│   │   │   ├── RegisterPage.jsx
│   │   │   └── RegisterPage.module.css
│   ├── App.css               # Main application styles
│   ├── App.jsx               # Root application component
│   ├── index.css             # Global styles
│   └── main.jsx              # Application entry point
├── .env                      # Environment variables
├── .gitignore                # Git ignore rules
├── eslint.config.js          # ESLint configuration
├── index.html                # HTML entry point
├── package-lock.json         # Dependency lock file
├── package.json              # Project dependencies and scripts
└── vite.config.js            # Vite build tool configuration

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