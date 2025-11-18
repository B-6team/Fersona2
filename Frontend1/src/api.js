// =============================
// ✅ axios 기본 설정
// =============================
import axios from "axios";

// -----------------------------
// 🔧 API 기본 URL 설정
// -----------------------------
const isLocal =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1";

const API_URL = isLocal
  ? "http://127.0.0.1:5000/fersona/api"       // 로컬 개발용
  : "https://13.60.90.230/fersona/api";       // ✅ 서버 배포용

// -----------------------------
// Axios 인스턴스
// -----------------------------
const axiosInstance = axios.create({
  baseURL: API_URL,
  withCredentials: false,
  timeout: 600000,
  validateStatus: (status) => status >= 200 && status < 500,
});

// ======================================================
// 1️⃣ 비디오 업로드 + 자동 분석 요청
// ======================================================
export const uploadMedia = async (
  videoBlob,
  audioBlob = null,
  userId = null,
  guestToken = null
) => {
  try {
    const formData = new FormData();

    if (videoBlob instanceof Blob)
      formData.append("video", videoBlob, "recording.webm");

    if (audioBlob instanceof Blob)
      formData.append("audio", audioBlob, "audio.wav");

    if (userId) formData.append("user_id", userId);
    if (guestToken) formData.append("guest_token", guestToken);

    console.log("[UPLOAD] 요청 시작:", `${API_URL}/upload`);

    const response = await axiosInstance.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    console.log("[UPLOAD] 성공:", response.data);
    return response.data; // ✅ result 구조 포함
  } catch (error) {
    console.error("[UPLOAD ERROR]", error.response?.data || error.message);
    throw error;
  }
};

// ======================================================
// 2️⃣ 분석 결과 조회 (✅ 엔드포인트 경로 수정됨)
// ======================================================
export const getAnalysisResult = async (userId) => {
  if (!userId) throw new Error("⚠️ userId가 필요합니다.");

  try {
    const url = `/result/${encodeURIComponent(userId)}`;
    console.log("[GET RESULT] 요청 시작:", `${API_URL}${url}`);

    const response = await axiosInstance.get(url);
    console.log("[GET RESULT] 성공:", response.data);

    return response.data.result; // ✅ result만 반환
  } catch (error) {
    console.error("[GET RESULT ERROR]", error.response?.data || error.message);
    throw error;
  }
};

// ======================================================
// 3️⃣ 서버 상태 확인 (테스트용)
// ======================================================
export const getStatus = async () => {
  try {
    const response = await axiosInstance.get("/status");
    console.log("[STATUS]", response.data);
    return response.data;
  } catch (error) {
    console.error("[STATUS ERROR]", error.response?.data || error.message);
    throw error;
  }
};

// ======================================================
// 4️⃣ 공통 에러 인터셉터
// ======================================================
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error(
      `[API ERROR] ${error.response?.status || "NO_STATUS"}:`,
      error.response?.data || error.message
    );
    return Promise.reject(error);
  }
);

export default axiosInstance;

