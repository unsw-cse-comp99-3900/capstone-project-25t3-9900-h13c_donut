### Test Coverage Details

#### Unit Tests (backend/tests/unit/)

The following modules have comprehensive unit tests with mocked external dependencies:

- **`core.security`** (`test_security.py`)
  - Password hashing and verification
  - JWT token creation and validation
  - Token expiration handling

- **`core.pubsub`** (`test_pubsub.py`)
  - Pub/Sub channel subscription/unsubscription
  - Message publishing to text and TTS channels
  - WebSocket connection handling

- **`services.asr_factory`** (`test_asr_factory.py`)
  - ASR service factory and service selection

- **`services.asr_openai_adapter`** (`test_asr_openai_adapter.py`)
  - OpenAI Whisper API integration (mocked)
  - API parameter construction
  - Error handling

- **`services.gpt_formatter`** (`test_gpt_formatter.py`)
  - GPT API calls for text formatting (mocked)
  - Fallback logic when GPT unavailable
  - Sentence splitting

- **`services.hallucination_detector`** (`test_hallucination_detector.py`)
  - Confidence analysis
  - Repetition detection
  - Semantic coherence checks

- **`services.diarization_matcher`** (`test_diarization_matcher.py`)
  - Sentence alignment with Whisper timestamps
  - Speaker assignment logic
  - Speaker change analysis

#### Integration Tests (backend/tests/integration/)

The following API routes have integration tests with real database interactions:

- **`routers/auth.py`** (`test_auth_routes.py`)
  - `POST /api/v1/auth/register` - User registration
  - `POST /api/v1/auth/login` - User login
  - `GET /api/v1/auth/me` - Get current user
  - `POST /api/v1/auth/logout` - User logout
  - `POST /api/v1/auth/check-reset` - Password reset verification
  - `POST /api/v1/auth/reset-password` - Password reset
  - `POST /api/v1/auth/change-password` - Change password

- **`routers/conversations.py`** (`test_conversations_routes.py`)
  - `GET /api/v1/conversations` - List conversations
  - `POST /api/v1/conversations` - Create conversation
  - `GET /api/v1/conversations/{cid}` - Get conversation details
  - `PATCH /api/v1/conversations/{cid}` - Rename conversation
  - `DELETE /api/v1/conversations/{cid}` - Delete conversation
  - `POST /api/v1/conversations/{cid}/segments` - Append transcript segment
  - Concurrent operations (race condition tests)

- **`routers/admin.py`** (`test_admin_routes.py`)
  - `GET /api/v1/admin/users` - List users
  - `GET /api/v1/admin/users/{user_id}` - Get user details
  - `PATCH /api/v1/admin/users/{user_id}` - Update user
  - `DELETE /api/v1/admin/users/{user_id}` - Delete user
  - `POST /api/v1/admin/users/{user_id}/reset-password` - Reset user password
  - `POST /api/v1/admin/keys/batch-generate` - Generate license keys
  - `GET /api/v1/admin/keys` - List license keys
  - `GET /api/v1/admin/keys/{key_id}` - Get key details
  - `DELETE /api/v1/admin/keys/{key_id}` - Delete license key
  - `POST /api/v1/admin/verify-key` - Verify license key

- **`routers/tts.py`** (`test_tts_routes.py`)
  - `POST /api/v1/tts/synthesize` - TTS synthesis (MelonTTS and ElevenLabs mocked)
  - Error handling (missing fields, generation failures)

- **WebSocket Routes** (`test_websocket_light.py`)
  - `/ws/upload-audio` - Connection establishment (lightweight only)
  - `/ws/asr-text` - Connection establishment (lightweight only)
  - `/ws/tts-audio` - Connection establishment (lightweight only)
  - Message format validation

#### Manual System Testing (External Service Dependencies)

The following components require manual system testing due to dependencies on external services, browser APIs, or real-time audio processing:

**1. Full Audio Streaming Pipeline** (`routers/ws_upload.py`)
- **Reason**: Requires real microphone access, Web Speech API, and full audio processing chain
- **Test Cases**:
  - **Case 1**: Real-time audio upload and transcription
    - Start recording → Speak → Stop recording
    - Verify: Audio uploaded, Web Speech text appears, Whisper transcription completes
  - **Case 2**: Multiple consecutive recordings
    - Record segment 1 → Stop → Record segment 2 → Stop
    - Verify: Both segments saved, sequence numbers correct
  - **Case 3**: Long recording session
    - Record for 30+ seconds with multiple sentences
    - Verify: All text captured, GPT formatting applied, diarization (if enabled) assigns speakers

**2. Real TTS Service Calls** (`services/tts_elevenlabs.py`)
- **Reason**: Requires valid ElevenLabs API key and network access
- **Test Cases**:
  - **Case 1**: ElevenLabs TTS with different accents
    - Select "paid" model → Choose accent → Request TTS
    - Verify: Audio generated, correct voice used, audio plays in browser
  - **Case 2**: TTS error handling
    - Use invalid API key → Request TTS
    - Verify: Error message displayed, system doesn't crash

**3. Real Diarization Service** (`services/diarization.py`)
- **Reason**: Requires pyannote.audio model files and significant processing time
- **Test Cases**:
  - **Case 1**: Multi-speaker conversation
    - Record conversation with 2+ speakers → Stop
    - Verify: Speakers correctly identified, speaker labels assigned to sentences
  - **Case 2**: Single speaker (should not create multiple speakers)
    - Record single speaker → Stop
    - Verify: All segments assigned to same speaker

**4. Real ASR Service Calls** (`services/asr_openai_adapter.py`)
- **Reason**: Requires valid OpenAI API key and network access (mocked in unit tests)
- **Test Cases**:
  - **Case 1**: Accurate transcription
    - Record clear speech → Stop
    - Verify: Transcription matches spoken words, timestamps accurate
  - **Case 2**: ASR error handling
    - Use invalid API key → Record → Stop
    - Verify: Error handled gracefully, user notified

**5. End-to-End Real-Time Flow**
- **Reason**: Requires full browser environment, microphone, and all external services
- **Test Cases**:
  - **Case 1**: Complete accent translation flow
    - Login → Select model/accent → Start recording → Speak → Stop → Play TTS
    - Verify: Web Speech shows text → Whisper improves it → GPT formats it → TTS plays in accent
  - **Case 2**: Concurrent users
    - Two users record simultaneously
    - Verify: Data isolation, no cross-user interference