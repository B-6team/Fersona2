import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useResult } from "context/ResultContext";
import styles from "./Interview.module.css";

// ----------------------------------
// ✅ 기본 질문 목록
// ----------------------------------
const QUESTIONS = [
  "자기소개를 해주세요.",
  "최근 가장 도전적이었던 일은 무엇인가요?",
  "팀 프로젝트에서 맡은 역할은 무엇이었나요?",
  "본인의 장점과 단점을 말해주세요.",
  "입사 후 이루고 싶은 목표는 무엇인가요?",
];

export default function Interview() {
  const navigate = useNavigate();
  const { setResult } = useResult(); // ✅ Context setter
  const videoRef = useRef(null);
  const mediaRef = useRef({ recorder: null, chunks: [], stream: null });
  const questionTimer = useRef(null);
  const timerRef = useRef(null); // ✅ 녹화 시간 타이머

  const [step, setStep] = useState("idle");
  const [sec, setSec] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [shuffledQuestions, setShuffledQuestions] = useState([]);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(true); // 데모용 로그인 상태

  // ✅ 시간 포맷 함수
  const toHHMMSS = (s) => {
    const h = Math.floor(s / 3600)
      .toString()
      .padStart(2, "0");
    const m = Math.floor((s % 3600) / 60)
      .toString()
      .padStart(2, "0");
    const sec = (s % 60).toString().padStart(2, "0");
    return `${h}:${m}:${sec}`;
  };

  // ✅ 카메라 / 마이크 스트림 확보
  const ensureStream = async () => {
    if (mediaRef.current.stream) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      mediaRef.current.stream = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch (err) {
      console.error("🎥 카메라 접근 실패:", err);
      alert("카메라/마이크 권한을 허용해주세요.");
    }
  };

  // ✅ 업로드 함수
  const uploadToServer = async () => {
    const { chunks } = mediaRef.current;
    if (!chunks?.length) {
      console.warn("⚠️ 업로드할 영상 데이터가 없습니다.");
      return;
    }

    const blob = new Blob(chunks, { type: "video/webm" });
    const formData = new FormData();
    formData.append("video", blob, "recording.webm");
    formData.append("user_id", "demo_user_123");

    try {
      const isLocal =
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1";

      const API_URL = isLocal
        ? "http://127.0.0.1:5000/upload"
        : "https://fersona.cloud/fersona/api/upload";

      console.log("🚀 업로드 시작:", API_URL);

      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error(`서버 응답 오류: ${response.status}`);

      const result = await response.json();
      console.log("✅ 업로드 성공:", result);

      if (result) {
        setResult(result.result || result);
        console.log("[Context] 분석 결과 저장 완료 ✅");
      }

      alert("✅ 영상 업로드 및 분석 완료!");
      navigate("/report-menu");
    } catch (err) {
      console.error("❌ 업로드 실패:", err);
      alert("⚠️ 업로드 중 오류가 발생했습니다. 콘솔을 확인해주세요.");
    }
  };

  // ✅ 질문 표시 (20초 간격, 랜덤)
  const startQuestionCycle = () => {
    if (questionTimer.current) clearInterval(questionTimer.current);

    const shuffled = [...QUESTIONS].sort(() => Math.random() - 0.5);
    setShuffledQuestions(shuffled);
    setCurrentQuestion(shuffled[0]);
    setQuestionIndex(0);

    questionTimer.current = setInterval(() => {
      setQuestionIndex((prev) => {
        const next = prev + 1;
        if (next >= shuffled.length) {
          clearInterval(questionTimer.current);
          setCurrentQuestion("");
          return prev;
        } else {
          setCurrentQuestion(shuffled[next]);
          return next;
        }
      });
    }, 20000);
  };

  // ✅ 녹화 시간 증가 타이머
  const startTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setSec(0);
    timerRef.current = setInterval(() => {
      setSec((prev) => prev + 1);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
  };

  // ✅ 녹화 시작
  const startNewRecording = async () => {
    await ensureStream();
    if (!mediaRef.current.stream) return;

    const rec = new MediaRecorder(mediaRef.current.stream);
    mediaRef.current.recorder = rec;
    mediaRef.current.chunks = [];

    rec.ondataavailable = (e) => e.data && mediaRef.current.chunks.push(e.data);
    rec.onstop = async () => {
      clearInterval(questionTimer.current);
      stopTimer();
      setIsRecording(false);
      await uploadToServer();
    };

    rec.start(1000);
    startQuestionCycle();
    startTimer();
    setIsRecording(true);
    setStep("recording");
  };

  // ✅ 일시 정지
  const handlePauseClick = () => {
    if (step === "recording") {
      mediaRef.current.recorder?.pause?.();
      stopTimer();
      clearInterval(questionTimer.current);
      setStep("paused");
      setIsRecording(false);
    }
  };

  // ✅ 녹화 종료
  const handleStopClick = () => {
    if (step === "recording" || step === "paused") {
      mediaRef.current.recorder?.stop?.();
      stopTimer();
      clearInterval(questionTimer.current);
      setStep("ended");
      setIsRecording(false);
    }
  };

  // ✅ 스트림 정리
  useEffect(() => {
    if (step !== "ended") return;
    const { stream } = mediaRef.current;
    stream?.getTracks()?.forEach((t) => t.stop());
    mediaRef.current.stream = null;
  }, [step]);

  // ---------------------------------
  // 🎨 렌더링
  // ---------------------------------
  return (
    <div className={styles.page}>
      <div className={styles.panel}>
        {/* 상단바 */}
        <div className={styles.topbar}>
          <div className={styles.chip}>
            <span className={styles.chipDot}></span>Persona Check
          </div>
          <div className={`${styles.timer} ${isRecording ? styles.onair : ""}`}>
            {toHHMMSS(sec)}
          </div>
        </div>

        {/* 질문 표시 */}
        {currentQuestion && (
          <div className={styles.questionBox}>{currentQuestion}</div>
        )}

        {/* 비디오 영역 */}
        <div className={styles.center}>
          <video
            className={styles.videoBox}
            ref={videoRef}
            autoPlay
            muted
            playsInline
          />
          {step === "ended" && (
            <button
              className={styles.reportBtn}
              onClick={() => navigate("/report-menu")}
            >
              리포트 확인하기
            </button>
          )}
        </div>

        {/* 버튼 */}
        <div className={styles.btnRow}>
          <button
            className={`${styles.btn} ${styles.btnPrimary} ${styles.sizeLg}`}
            onClick={startNewRecording}
            disabled={isRecording}
          >
            녹화 시작하기
          </button>
          <button
            className={`${styles.btn} ${styles.btnGhost} ${styles.sizeLg}`}
            onClick={handlePauseClick}
            disabled={!isRecording}
          >
            일시 정지
          </button>
          <button
            className={`${styles.btn} ${styles.btnDanger} ${styles.sizeLg}`}
            onClick={handleStopClick}
            disabled={step === "idle" || step === "ended"}
          >
            녹화 종료하기
          </button>
        </div>
      </div>

      {/* 로그인 필요 모달 */}
      {showLoginPrompt && (
        <div className={styles.modalBackdrop}>
          <div className={styles.modal}>
            <button
              className={styles.modalX}
              onClick={() => setShowLoginPrompt(false)}
            >
              ×
            </button>
            <div className={styles.modalBody}>
              <div className={styles.modalTitle}>로그인이 필요합니다.</div>
              <button
                className={`${styles.btn} ${styles.btnPrimary}`}
                onClick={() => {
                  setIsLoggedIn(true);
                  setShowLoginPrompt(false);
                }}
              >
                로그인 계속하기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

