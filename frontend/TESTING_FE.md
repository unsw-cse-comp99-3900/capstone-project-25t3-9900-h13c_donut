**Frontend – what is covered**

We have implemented comprehensive testing for the frontend:

**Component-level tests**
- Reusable UI components (buttons, forms, layout components)
  - `MessageBox` component (~90% coverage)
  - Form validation and error display components

**Page-level tests**
- Authentication pages (`LoginPage`, `RegisterPage`, `ForgotPasswordPage`)
  - Form rendering and user interactions
  - Form validation and error messaging
  - Navigation and state management
  - Coverage: ~85% for login/register flows
- Admin pages (`AdminDashboard`, `AdminUserManagement`, `AdminKeyManagement`)
  - Rendering and basic management interactions
  - User and license key CRUD operations
  - Role-based access control
  - Coverage: High coverage for admin operations
- Dashboard (`Dashboard`)
  - Start/stop streaming button behaviour
  - Conversation selection and title display
  - Model/accent selector behaviour (state changes)
  - Conversation CRUD operations (create, rename, delete, switch)
  - Coverage: Key logic covered (~70% branches, core interactions tested)

**Utility functions and configuration**
- `utils/validators.js` - Input validation (~95% coverage)
- `config/api.js` - API request handling and error management
- `api/auth.js` - Authentication API functions

**Key coverage areas**
- User login / registration flow (complete flow testing)
- Admin page operations (user management, license key management)
- Dashboard core interactions (start/stop, conversation switching, accent & model selection)

**Test coverage summary**
- **Overall**: Statements ~55.57%, Branches ~83.37%, Functions ~53.94%, Lines ~55.57%
- **Components**: ~100% coverage (MessageBox and other shared components)
- **Utils/Config**: ~95% coverage (validators, API configuration)
- **Admin/Login pages**: High coverage (~85-90% for critical paths)
- **Dashboard**: Core logic covered (~70% branches, key interactions tested)

**Why streaming parts are not fully automated**

Real-time audio capture, Web Speech API, MediaRecorder, and raw WebSocket streaming are not fully automated because:

1. **Browser API limitations in CI**
   - Microphone access (`navigator.mediaDevices.getUserMedia`) requires user permission and real hardware
   - Web Speech API (`webkitSpeechRecognition`) is browser-specific and unstable in headless environments
   - MediaRecorder API behavior varies across browsers and CI environments

2. **WebSocket streaming complexity**
   - Real-time audio streaming over WebSockets requires continuous connection and binary data handling
   - Difficult to mock accurately in test environments
   - Timing-dependent behavior is hard to verify programmatically

3. **Our testing approach**
   - **Pure logic is unit tested**: Text processing, TTS request logic, state management
   - **Component behavior is tested**: Button clicks, state changes, UI updates (with mocked WebSocket/APIs)
   - **Browser-dependent parts use manual testing**: Real microphone, Web Speech API, live WebSocket connections
   - **Manual test cases documented**: See "System / End-to-end Testing (Manual)" section below