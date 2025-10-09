import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LoginPage from "./pages/Login/LoginPage";
import Dashboard from "./pages/Dashboard/Dashboard";

function App() {
  return (
    <Router>
      <Routes>
        {/* Default and only route → Login page */}
        <Route path="/" element={<LoginPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
