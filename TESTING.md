# Testing Guide

This document provides comprehensive instructions on how to run, view, and use tests for both the frontend and backend of the Fast Accent Translator project.

## Table of Contents

- [Overview](#overview)
- [Backend Testing](#backend-testing)
  - [Prerequisites](#backend-prerequisites)
  - [Running Tests](#running-backend-tests)
  - [Viewing Coverage Reports](#viewing-backend-coverage)
  - [Test Structure](#backend-test-structure)
- [Frontend Testing](#frontend-testing)
  - [Prerequisites](#frontend-prerequisites)
  - [Running Tests](#running-frontend-tests)
  - [Viewing Coverage Reports](#viewing-frontend-coverage)
  - [Test Structure](#frontend-test-structure)
- [Test Coverage Summary](#test-coverage-summary)
- [Manual System Testing](#manual-system-testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

The project includes comprehensive automated tests for both frontend and backend components:

- **Backend**: Unit tests and integration tests using `pytest`
- **Frontend**: Unit tests, component tests, and integration tests using `Vitest` and `React Testing Library`

Both test suites cover happy paths, error cases, and edge conditions. External APIs are mocked to ensure fast, reliable, and cost-effective testing.

---

## Backend Testing

### Backend Prerequisites

1. **Python 3.9+** installed
2. **Dependencies installed**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Test dependencies** (included in `requirements.txt`):
   - `pytest`
   - `pytest-asyncio`
   - `pytest-cov`
   - `httpx`
   - `faker`

### Running Backend Tests

#### Run All Tests

```bash
cd backend
pytest
```

#### Run Specific Test File

```bash
# Run a specific unit test file
pytest tests/unit/test_security.py

# Run a specific integration test file
pytest tests/integration/test_auth_routes.py
```

#### Run Tests by Category

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

#### Run Tests with Verbose Output

```bash
# Show detailed output for each test
pytest -v

# Show even more details (print statements, etc.)
pytest -v -s
```

#### Run Tests Matching a Pattern

```bash
# Run tests matching a keyword
pytest -k "auth"

# Run tests matching a pattern
pytest -k "test_login or test_register"

# Run race condition/concurrency tests
pytest -k "concurrent"
```

### Viewing Backend Coverage

#### Generate Coverage Report

```bash
cd backend
pytest --cov=app --cov-report=html --cov-report=term
```

This command will:
- Run all tests
- Generate a **terminal report** showing coverage percentages
- Generate an **HTML report** in `backend/htmlcov/index.html`

#### View HTML Coverage Report

1. Generate the coverage report (see above)
2. Open `backend/htmlcov/index.html` in your browser
3. Navigate through the report to see:
   - Overall coverage statistics
   - Coverage by module/file
   - Line-by-line coverage highlighting (green = covered, red = not covered)

#### Coverage Goals

- **Core Business Logic**: ≥80%
- **REST API Endpoints**: 100% (all endpoints have at least one test)
- **Service Layer**: ≥70%
- **Overall**: ≥70%

### Backend Test Structure

```
backend/tests/
├── conftest.py              # Pytest fixtures (test database, HTTP client, etc.)
├── unit/                    # Unit tests (pure logic, no external dependencies)
│   ├── test_security.py     # Password hashing, JWT tokens
│   ├── test_pubsub.py       # Pub/Sub message queue
│   ├── test_hallucination_detector.py  # ASR hallucination detection
│   ├── test_asr_factory.py  # ASR service factory
│   ├── test_asr_openai_adapter.py  # OpenAI Whisper adapter
│   ├── test_gpt_formatter.py  # GPT text formatting (includes fallback)
│   └── test_diarization_matcher.py  # Speaker diarization matching
└── integration/             # Integration tests (REST API, WebSocket, database)
    ├── test_auth_routes.py  # Authentication endpoints
    ├── test_conversations_routes.py  # Conversation CRUD operations + race condition tests
    ├── test_tts_routes.py   # TTS synthesis endpoints
    ├── test_admin_routes.py  # Admin user and key management
    └── test_websocket_light.py  # Lightweight WebSocket tests
```

#### Test Types

- **Unit Tests**: Test individual functions/classes in isolation with mocked dependencies
- **Integration Tests**: Test API endpoints with real database (in-memory SQLite) and mocked external APIs
- **Concurrency/Race Condition Tests**: Test concurrent operations to detect race conditions and ensure data consistency

#### Running Concurrency Tests

The project includes comprehensive race condition and concurrency tests in `test_conversations_routes.py`:

```bash
# Run all concurrency tests
pytest tests/integration/test_conversations_routes.py -k "concurrent" -v

# Run specific concurrency test
pytest tests/integration/test_conversations_routes.py::test_concurrent_conversation_creation -v
```

**Concurrency Test Scenarios:**
- `test_concurrent_conversation_creation`: Tests concurrent creation of multiple conversations
- `test_concurrent_conversation_update`: Tests concurrent updates to the same conversation
- `test_concurrent_segment_append`: Tests concurrent segment appends (detects sequence number race conditions)
- `test_concurrent_mixed_operations`: Tests concurrent read, update, and append operations
- `test_concurrent_user_isolation`: Tests concurrent operations by different users (data isolation)
- `test_concurrent_delete_and_access`: Tests race conditions when deleting while accessing

These tests use `asyncio.gather()` to execute multiple requests concurrently and verify:
- All operations complete successfully
- Data consistency is maintained
- User isolation is preserved
- Race conditions are detected and documented

---

## Frontend Testing

### Frontend Prerequisites

1. **Node.js 18+** installed
2. **Dependencies installed**:
   ```bash
   cd frontend
   npm install
   ```

3. **Test dependencies** (included in `package.json`):
   - `vitest`
   - `@testing-library/react`
   - `@testing-library/user-event`
   - `@testing-library/jest-dom`
   - `jsdom`
   - `@vitest/coverage-v8`

### Running Frontend Tests

#### Run Tests in Watch Mode

```bash
cd frontend
npm run test
```

This will:
- Run all tests
- Watch for file changes and re-run tests automatically
- Show results in the terminal

#### Run Tests with UI

```bash
cd frontend
npm run test:ui
```

This will:
- Open a browser-based test UI
- Show test results in an interactive interface
- Allow you to filter, search, and debug tests visually

#### Run Tests Once (No Watch)

```bash
cd frontend
npm run test -- --run
```

#### Run Specific Test File

```bash
cd frontend
npm run test -- src/pages/Login/__tests__/LoginPage.test.jsx
```

#### Run Tests Matching a Pattern

```bash
cd frontend
npm run test -- -t "login"
```

### Viewing Frontend Coverage

#### Generate Coverage Report

```bash
cd frontend
npm run test:coverage
```

This command will:
- Run all tests
- Generate a **terminal report** showing coverage percentages
- Generate an **HTML report** in `frontend/coverage/index.html`

#### View HTML Coverage Report

1. Generate the coverage report (see above)
2. Open `frontend/coverage/index.html` in your browser
3. Navigate through the report to see:
   - Overall coverage statistics (statements, branches, functions, lines)
   - Coverage by file/directory
   - Line-by-line coverage highlighting

#### Coverage Goals

- **Unit Tests**: >90% coverage for utility functions
- **Component Tests**: >80% coverage for React components
- **Integration Tests**: Critical user flows (login, registration, password reset)
- **Overall**: >80% for tested modules

### Frontend Test Structure

```
frontend/src/
├── utils/
│   ├── validators.js
│   └── __tests__/
│       └── validators.test.js
├── components/
│   ├── MessageBox.jsx
│   └── __tests__/
│       └── MessageBox.test.jsx
├── config/
│   ├── api.js
│   └── __tests__/
│       └── api.test.js
├── api/
│   ├── auth.js
│   └── __tests__/
│       └── auth.test.js
└── pages/
    ├── Login/
    │   ├── LoginPage.jsx
    │   └── __tests__/
    │       └── LoginPage.test.jsx
    ├── Register/
    │   ├── RegisterPage.jsx
    │   └── __tests__/
    │       └── RegisterPage.test.jsx
    ├── ForgotPassword/
    │   ├── ForgotPasswordPage.jsx
    │   └── __tests__/
    │       └── ForgotPasswordPage.test.jsx
    ├── Dashboard/
    │   ├── Dashboard.jsx
    │   └── __tests__/
    │       └── Dashboard.test.jsx
    └── Admin/
        ├── AdminDashboard.jsx
        ├── AdminUserManagement.jsx
        ├── AdminKeyManagement.jsx
        └── __tests__/
            ├── AdminDashboard.test.jsx
            ├── AdminUserManagement.test.jsx
            └── AdminKeyManagement.test.jsx
```

#### Test Types

- **Unit Tests**: Test utility functions in isolation
- **Component Tests**: Test React component rendering, user interactions, and state management
- **Integration Tests**: Test API integration, routing, and authentication flows

---

## Test Coverage Summary

### Backend Coverage

**What is Covered:**
- ✅ Authentication flows (register, login, password reset)
- ✅ Conversation management (CRUD operations)
- ✅ Admin features (user management, license keys)
- ✅ Service layer logic (ASR, GPT formatting, diarization)
- ✅ Security (password hashing, JWT tokens)
- ✅ Pub/Sub messaging system
- ✅ Race conditions and concurrency
  - Concurrent conversation creation, updates, and deletions
  - Concurrent segment appends to the same conversation
  - Concurrent mixed operations (read, update, append)
  - Concurrent user isolation and access control
  - Race condition detection (e.g., sequence number calculation)

**Partial/Manual Coverage:**
- ⚠️ Full WebSocket audio streaming pipeline (lightweight tests + manual E2E)
- ⚠️ Real external API calls (mocked in tests, verified manually)

### Frontend Coverage

**What is Covered:**
- ✅ Authentication pages (login, register, forgot password)
- ✅ Form validation and error handling
- ✅ Component rendering and user interactions
- ✅ API integration (mocked)
- ✅ Routing and navigation
- ✅ Admin dashboard components

**Partial/Manual Coverage:**
- ⚠️ Real-time audio capture and Web Speech API (mocked in tests)
- ⚠️ WebSocket streaming (mocked in tests, verified manually)
- ⚠️ Browser-specific features (manual testing required)

---

## Manual System Testing

Some components (real-time audio streaming, browser APIs, external service calls) are difficult to fully automate. These are covered via manual end-to-end testing.

### Test Environment Setup

1. **Backend**: Run `uvicorn app.main:app --reload` on port 8000
2. **Frontend**: Run `npm run dev` on port 5173
3. **Browser**: Chrome (latest stable version)
4. **External Services**: Valid API keys for OpenAI and ElevenLabs

### Manual Test Scenarios

#### 1. Basic Login + Dashboard Access

**Steps:**
1. Start backend and frontend servers
2. Open app in browser and navigate to login page
3. Log in with valid credentials
4. Navigate to Dashboard

**Expected:**
- Login succeeds, JWT stored
- Dashboard loads conversation list
- No backend errors in logs

#### 2. Free Model: Real-time Accent Translation

**Steps:**
1. On Dashboard, select model = `free` and choose an accent
2. Click `Start` to begin streaming
3. Allow microphone access when prompted
4. Speak a short English sentence (5-10 seconds)
5. Click `Stop`

**Expected:**
- Web Speech preview shows interim and final text
- TTS segments play back in selected accent
- New conversation appears in list
- Final transcripts saved in database

#### 3. Paid Model: TTS via ElevenLabs

**Steps:**
1. On Dashboard, select model = `paid` and choose an accent
2. Repeat speaking steps from Scenario 2

**Expected:**
- TTS uses configured ElevenLabs voice
- No server-side errors
- Transcripts stored correctly

#### 4. Admin: Role-based Access Control

**Steps:**
1. Log in as normal user, attempt to access Admin page
2. Log in as admin user, access Admin page

**Expected:**
- Normal user receives 403 / "not authorized"
- Admin user can view user list and license keys

#### 5. Error Handling (Network/API Failures)

**Steps:**
1. Temporarily invalidate OpenAI/ElevenLabs API key or block network
2. Start translation session and trigger TTS/ASR
3. Restore correct configuration

**Expected:**
- Frontend shows error message (does not crash)
- Backend logs contain clear error messages
- System recovers once API key/network is fixed

---

## Troubleshooting

### Backend Test Issues

#### Tests Fail with Database Errors

**Problem**: `UndefinedTableError` or database connection errors

**Solution**:
- Ensure test database is properly initialized in `conftest.py`
- Check that Tortoise ORM models are imported correctly
- Run `pytest` from the `backend/` directory

#### Tests Fail with Import Errors

**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
- Ensure you're running tests from the `backend/` directory
- Check that `PYTHONPATH` includes the project root
- Verify all dependencies are installed: `pip install -r requirements.txt`

#### Coverage Report Not Generated

**Problem**: `pytest: error: unrecognized arguments: --cov`

**Solution**:
- Install coverage tools: `pip install pytest-cov`
- Run with coverage: `pytest --cov=app --cov-report=html`

### Frontend Test Issues

#### Tests Fail Due to localStorage

**Problem**: Tests fail because of leftover localStorage data

**Solution**:
- Clear localStorage in test `beforeEach` hooks
- Ensure tests clean up after themselves

#### Mock Not Working

**Problem**: Mocked functions not being called or returning wrong values

**Solution**:
- Ensure `vi.mock()` is called **before** imports
- Reset mocks in `beforeEach`: `mockFn.mockReset()`
- Check that mock paths match actual import paths

#### Async Test Timing Issues

**Problem**: Tests fail with "element not found" or timeout errors

**Solution**:
- Use `waitFor()` for async assertions:
  ```javascript
  await waitFor(() => {
    expect(screen.getByText('Success')).toBeInTheDocument()
  })
  ```
- Increase timeout if needed: `waitFor(..., { timeout: 3000 })`

#### Router Navigation Not Working

**Problem**: `useNavigate` not working in tests

**Solution**:
- Mock `react-router-dom`:
  ```javascript
  vi.mock('react-router-dom', () => ({
    useNavigate: () => mockNavigate,
  }))
  ```
- Or wrap component in `<BrowserRouter>` in test setup

---

## Quick Reference

### Backend

```bash
# Run all tests
cd backend && pytest

# Run with coverage
cd backend && pytest --cov=app --cov-report=html --cov-report=term

# View coverage
open backend/htmlcov/index.html
```

### Frontend

```bash
# Run tests (watch mode)
cd frontend && npm run test

# Run tests with UI
cd frontend && npm run test:ui

# Run with coverage
cd frontend && npm run test:coverage

# View coverage
open frontend/coverage/index.html
```

---

## Additional Resources

- **Backend Testing**: See `backend/tests/` directory for detailed test documentation
- **Frontend Testing**: See `frontend/TESTING_BE.md` directory for detailed test documentation
- **Vitest Documentation**: https://vitest.dev/
- **Pytest Documentation**: https://docs.pytest.org/
- **React Testing Library**: https://testing-library.com/react

---

## Notes

- Generated coverage artifacts and caches are excluded from version control (see `.gitignore`).
- All test code is kept in the repository so that testers can run the full test suite.
- External APIs (OpenAI, ElevenLabs) are mocked in automated tests
- Test database uses in-memory SQLite for fast, isolated tests
- Coverage reports are generated locally and not committed to the repository

