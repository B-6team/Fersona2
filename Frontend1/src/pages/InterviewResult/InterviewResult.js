// src/pages/InterviewResult/InterviewResult.js
import React from "react";
import { Routes, Route } from "react-router-dom";

import ResultReportCheck from "./Check/ResultReportCheck/ResultReportCheck";
import IgnitionFeedbackCheck from "./Check/IgnitionFeedback/IgnitionFeedbackCheck";
import VideoPlayCheck from "./Check/VideoPlayCheck/VideoPlayCheck";

import { ResultProvider } from "../../context/ResultContext";

export default function InterviewResult() {
  return (
    <ResultProvider>
      <Routes>
        {/* 결과 리포트 */}
        <Route path="result-report" element={<ResultReportCheck />} />

        {/* 발화/억양 피드백 */}
        <Route path="feedback-report" element={<IgnitionFeedbackCheck />} />

        {/* 비디오 재생 */}
        <Route path="play-video/:videoId" element={<VideoPlayCheck />} />

        {/* 기본 요약 페이지 */}
        <Route
          index
          element={
            <div style={{ padding: 40 }}>
              <h2>면접 결과 요약 페이지</h2>
              <p>왼쪽 메뉴 또는 버튼을 통해 상세 리포트로 이동하세요.</p>
            </div>
          }
        />
      </Routes>
    </ResultProvider>
  );
}

