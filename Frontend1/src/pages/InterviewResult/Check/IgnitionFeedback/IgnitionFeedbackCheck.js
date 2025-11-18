import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import styles from "./IgnitionFeedbackCheck.module.css";
import { useResult } from "context/ResultContext";

// ✅ Chart.js 설정 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function FeedbackReport() {
  const navigate = useNavigate();
  const audioRef = useRef(null);
  const [showDetails, setShowDetails] = useState(false);

  // ✅ 분석 결과 Context 불러오기
  const context = useResult() || {};
  const result = context.result || {};
  const whisper = result.whisper || {};
  const report = result.report || {};

  // ✅ Whisper 피드백 데이터
  const speechFeedbackData = Array.isArray(whisper.feedback?.speech)
    ? whisper.feedback.speech
    : [];
  const pitchFeedbackData = Array.isArray(whisper.feedback?.pitch)
    ? whisper.feedback.pitch
    : [];

  // ✅ 비정상 구간만 필터링
  const abnormalSpeechData = speechFeedbackData.filter(
    (d) => d.wpm_label === -1 || d.wpm_label === 1
  );
  const abnormalPitchData = pitchFeedbackData.filter(
    (d) =>
      d.feedback?.includes("억양 변화") ||
      d.feedback?.includes("단조") ||
      d.feedback?.includes("억양이 낮습니다")
  );

  // ✅ 그래프 데이터 (발화 속도 변화)
  const duration = whisper.duration_sec || whisper.duration || 0;
  const interval = 5;
  const timeLabels = [];
  for (let i = 0; i <= duration; i += interval) {
    timeLabels.push(`${i}~${i + interval}s`);
  }

  const chartValues = timeLabels.map((_, idx) => {
    const start = idx * interval;
    const end = start + interval;
    const inRange = speechFeedbackData.filter(
      (item) => item.start_time >= start && item.end_time <= end
    );
    if (inRange.length === 0) return 0;
    const avg = inRange.reduce((sum, cur) => sum + (cur.wpm_label ?? 0), 0);
    return avg / inRange.length;
  });

  const data = {
    labels: timeLabels,
    datasets: [
      {
        label: "발화 속도 변화",
        data: chartValues,
        borderColor: "#007bff",
        backgroundColor: "rgba(0,0,0,0)",
        fill: false,
        tension: 0.3,
        pointRadius: 3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        title: { display: true, text: "시간 구간 (초)" },
        ticks: { color: "#333" },
      },
      y: {
        title: { display: true, text: "발화 속도 라벨 (-1: 느림, 0: 보통, 1: 빠름)" },
        min: -1,
        max: 1,
        ticks: { stepSize: 0.5, color: "#333" },
      },
    },
    plugins: { legend: { display: false } },
  };

  // ✅ 시선 및 표정 피드백 (새 구조)
  const gazeFeedback = {
    center: report.gaze_center_feedback
      ? {
          feedback: report.gaze_center_feedback,
          cause: report.gaze_center_cause,
          correction: report.gaze_center_correction,
        }
      : null,
    blink: report.blink_feedback
      ? {
          feedback: report.blink_feedback,
          cause: report.blink_cause,
          correction: report.blink_correction,
        }
      : null,
  };

  const expressionFeedback = report.expression_feedback
    ? {
        feedback: report.expression_feedback,
        cause: report.expression_cause,
        correction: report.expression_correction,
      }
    : null;

  const audioFile = result.audio_file || null;

  // ✅ 피드백 유무 확인
  const hasData =
    abnormalSpeechData.length > 0 ||
    abnormalPitchData.length > 0 ||
    gazeFeedback.center ||
    gazeFeedback.blink ||
    expressionFeedback;

  if (!hasData) {
    return (
      <div className={styles.reportContainer}>
        <div className={styles.reportNav}>
          <button className={styles.reportBackButton} onClick={() => navigate(-1)}>
            ← 돌아가기
          </button>
          <button
            className={styles.reportMainButton}
            onClick={() => setShowDetails(!showDetails)}
          >
            📄 피드백 확인하기
          </button>
        </div>

        <main className={styles.contentBgGray}>
          <div className={styles.contentBgWhite}>
            <p className={styles.feedbackContentArea}>
              ⚠️ 피드백 데이터가 없습니다. 분석을 다시 시도해주세요.
            </p>
          </div>
        </main>
      </div>
    );
  }

  // ✅ 오디오 구간 재생
  const playSegment = (start, end) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = start;
    audio.play();
    const stopAt = () => {
      if (audio.currentTime >= end) {
        audio.pause();
        audio.removeEventListener("timeupdate", stopAt);
      }
    };
    audio.addEventListener("timeupdate", stopAt);
  };

  // ✅ 렌더링
  return (
    <div className={styles.reportContainer}>
      <div className={styles.reportNav}>
        <button className={styles.reportBackButton} onClick={() => navigate(-1)}>
          ← 돌아가기
        </button>
        <button
          className={styles.reportMainButton}
          onClick={() => setShowDetails(!showDetails)}
        >
          📌 피드백 자세히 보기
        </button>
      </div>

      <main className={styles.contentBgGray}>
        <div className={styles.contentBgWhite}>
          {/* 🔹 발화 속도 그래프 */}
          <div className={styles.contentBgBlue} style={{ height: "320px" }}>
            <Line data={data} options={options} />
          </div>

          {showDetails && (
            <div className={styles.feedbackDetail}>
              {audioFile && <audio ref={audioRef} src={audioFile} controls hidden />}

              {/* ✅ 발화 속도 피드백 */}
              {abnormalSpeechData.map((item, idx) => (
                <div key={`speech-${idx}`} className={styles.feedbackItem}>
                  <p><strong>구간:</strong> {item.start_time} ~ {item.end_time}초</p>
                  <p><strong>피드백:</strong> {item.feedback}</p>
                  <p><strong>개선:</strong> {item.correction}</p>
                  {audioFile && (
                    <button
                      onClick={() => playSegment(item.start_time, item.end_time)}
                      className={styles.playSegmentButton}
                    >
                      ▶️ 재생
                    </button>
                  )}
                </div>
              ))}

              {/* ✅ 억양 피드백 */}
              {abnormalPitchData.map((item, idx) => (
                <div key={`pitch-${idx}`} className={styles.feedbackItem}>
                  <p><strong>구간:</strong> {item.start_time} ~ {item.end_time}초</p>
                  <p><strong>피드백:</strong> {item.feedback}</p>
                  <p><strong>개선:</strong> {item.correction}</p>
                </div>
              ))}

              {/* ✅ 시선 (중앙 응시율 + 깜빡임) */}
              {gazeFeedback.center && (
                <div className={styles.feedbackItem}>
                  <p><strong>시선(중앙 응시율):</strong> {gazeFeedback.center.feedback}</p>
                  <p><strong>원인:</strong> {gazeFeedback.center.cause}</p>
                  <p><strong>개선:</strong> {gazeFeedback.center.correction}</p>
                </div>
              )}
              {gazeFeedback.blink && (
                <div className={styles.feedbackItem}>
                  <p><strong>시선(깜빡임):</strong> {gazeFeedback.blink.feedback}</p>
                  <p><strong>원인:</strong> {gazeFeedback.blink.cause}</p>
                  <p><strong>개선:</strong> {gazeFeedback.blink.correction}</p>
                </div>
              )}

              {/* ✅ 표정 피드백 */}
              {expressionFeedback && (
                <div className={styles.feedbackItem}>
                  <p><strong>표정:</strong> {expressionFeedback.feedback}</p>
                  <p><strong>원인:</strong> {expressionFeedback.cause}</p>
                  <p><strong>개선:</strong> {expressionFeedback.correction}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

