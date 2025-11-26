# Testing

> **For detailed testing instructions, see [TESTING.md](TESTING.md)**

The [TESTING.md](TESTING.md) guide provides comprehensive instructions on:
- How to run frontend and backend tests
- How to view coverage reports
- Test structure and organization
- Manual system testing scenarios
- Troubleshooting common issues

---

### Summary of What is Tested

Overall, automated tests cover roughly 50–60% of the frontend and backend codebase, with core
routers and service modules typically above 70–90% coverage. Heavily I/O-bound and
browser-specific parts are covered via manual system tests instead of full automation.

**Backend – what is covered**

- Authentication flows  
  - Register, login, and `whoami` endpoints  
  - Password hashing and token verification logic
- Conversation management  
  - Create, list, get details, and delete conversations  
  - Per-user data isolation (users cannot access others’ conversations)
- Admin features  
  - Admin-only endpoints with role-based access control
- Service layer logic  
  - ASR service factory and OpenAI ASR adapter (mocked external API)  
  - Hallucination detection rules (repetition, low confidence, noise)  
  - GPT formatter fallback and sentence splitting  
  - Basic diarization matching between timestamps and speaker IDs
- Infrastructure  
  - Pub/sub channel used by WebSocket text/TTS  
  - Database initialisation using a dedicated test SQLite database
- Race conditions and concurrency  
  - Concurrent conversation creation, updates, and deletions  
  - Concurrent segment appends to the same conversation  
  - Concurrent mixed operations (read, update, append)  
  - Concurrent user isolation and access control  
  - Race condition detection (e.g., sequence number calculation in segment appends)

**Backend – partial / manual coverage**

- Full streaming audio pipeline in `ws_upload.py`  
  - Control messages (`start` / `stop`) and basic error paths are tested via lightweight WebSocket tests  
  - End-to-end audio → ASR → diarization → database → transcript refresh is validated via manual system tests
- `tts_elevenlabs.py`  
  - Core logic is exercised indirectly through the `/api/v1/tts/synthesize` endpoint with TTS backends mocked  
  - Real external calls to ElevenLabs are verified manually (see System / End-to-end Testing)

> **For detailed testing instructions, see [TESTING_BE.md](tests\backend\TESTING_BE.MD)**
---

**Frontend – what is covered**

- Auth pages and flows  
  - Login / register / forgot password components and user interactions  
  - Form validation and error messaging
- Shared components and utilities  
  - Reusable UI components (buttons, forms, layout)  
  - Utility functions (text helpers, config handling)
- Admin page  
  - Rendering and basic management interactions
- Dashboard (accent translator) – core behaviour  
  - Start/stop streaming button behaviour  
  - Conversation selection and title display  
  - Model/accent selector behaviour (state changes)

**Frontend – partial / manual coverage**

- Real-time audio capture, Web Speech API, and raw WebSocket streaming  
  - These are not fully automated in tests  
  - In automated tests, browser APIs and WebSocket clients are mocked; we only verify component state and UI responses  
  - Full real-time flows are covered via manual scenarios described below
> **For detailed testing instructions, see [TESTING_FE.md](tests\frontend\TESTING_FE.md)**
---

### System / End-to-end Testing (Manual)

Some parts of the system (microphone access, the browser Web Speech API, real-time audio
streaming over WebSockets, and live calls to external ASR/TTS providers) are difficult to
fully automate in CI. For these components, we complement automated tests with manual
end-to-end scenarios.

#### Test environment

- Browser: Chrome (latest stable version)
- Backend: FastAPI dev server (`uvicorn app.main:app --reload`)
- Frontend: React dev server (`npm run dev`)
- External services:
  - OpenAI Whisper / GPT (valid API key)
  - ElevenLabs TTS (for paid model tests)
  - Local MeloTTS (for free model tests)

#### E2E Test Scenarios

#### 1. Basic login + Dashboard access

- **Steps**
  1. Start backend and frontend dev servers.
  2. Open the app in Chrome and navigate to the login page.
  3. Log in with a valid user.
  4. Navigate to the Dashboard.

- **Expected**
  - Login succeeds and a JWT is stored.
  - Dashboard loads the conversation list (empty for a new user).
  - No backend errors appear in the logs.

#### 2. Free model: real-time accent translation

- **Steps**
  1. On the Dashboard, select model = `free` and choose an accent.
  2. Click `Start` to begin streaming.
  3. Allow microphone access when prompted.
  4. Speak a short English sentence (5–10 seconds).
  5. Click `Stop`.

- **Expected**
  - Web Speech preview shows interim and final text while speaking.
  - Short TTS segments are played back in the selected accent.
  - A new conversation appears in the list.
  - Opening the conversation shows final transcripts saved in the database.

#### 3. Paid model: TTS via ElevenLabs

- **Steps**
  1. On the Dashboard, select model = `paid` and choose another accent.
  2. Repeat the same speaking steps as in Scenario 2.

- **Expected**
  - TTS uses the configured ElevenLabs voice.
  - No unhandled server-side errors occur when calling the external API.
  - Transcripts are still stored correctly.

#### 4. Admin: role-based access control

- **Steps**
  1. Log in as a normal user and attempt to access the Admin page or `/api/v1/admin/...` routes.
  2. Log in as an admin user and access the same routes.

- **Expected**
  - Normal user receives 403 / “not authorised”.
  - Admin user can view the user list / license keys as expected.

#### 5. Error handling (network / API failures)

- **Steps**
  1. Temporarily invalidate the OpenAI/ElevenLabs API key or block network access.
  2. Start a translation session and trigger TTS / ASR.
  3. Restore the correct configuration afterwards.

- **Expected**
  - The frontend shows an error message or at least does not crash.
  - Backend logs contain a clear error for the external API failure.
  - The system recovers once the API key / network is fixed.
