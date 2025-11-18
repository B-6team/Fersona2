import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";

import Home from "./pages/Home/Home.js";
import MainPage from "./pages/InterviewResult/MainPage.js";
import InterviewResult from "./pages/InterviewResult/InterviewResult.js";
import InterviewReport from "./pages/InterviewResult/Check/ResultReportCheck/ResultReportCheck.js";
import FeedbackReport from "./pages/InterviewResult/Check/IgnitionFeedback/IgnitionFeedbackCheck.js";
import VideoPlayerPage from "./pages/InterviewResult/Check/VideoPlayCheck/VideoPlayCheck.js";

import Connection from "./pages/Connection/Connection.js";
import Interview from "./pages/Interview/Interview.js";
import Header from "./components/Header/Header.js";
import { Check } from "lucide-react";

// ✅ Context Provider import
import { ResultProvider } from "./context/ResultContext.js";

function AppWrapper() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const location = useLocation();

  const toggleLogin = () => setIsLoggedIn(!isLoggedIn);
  const shouldShowHeader = location.pathname !== '/';

  return (
    <>
      {shouldShowHeader && <Header isLoggedIn={isLoggedIn} toggleLogin={toggleLogin} />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/report-menu" element={<MainPage />} />
        <Route path="/interview-result" element={<InterviewResult />} />
        <Route path="/interview-result/interview-report" element={<InterviewReport />} />
        <Route path="/interview-result/feedback-report" element={<FeedbackReport />} />
        <Route path="/interview-result/play-video/:videoId?" element={<VideoPlayerPage />} />
        <Route path="/connection" element={<Connection />} />
        <Route path="/interview" element={<Interview />} />
        <Route path="/check" element={<Check />} />
      </Routes>
    </>
  );
}

function App() {
  return (
    <ResultProvider>
      <Router>
        <AppWrapper />
      </Router>
    </ResultProvider>
  );
}

export default App;
