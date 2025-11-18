import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useResult } from "context/ResultContext";
import styles from "./VideoPlayCheck.module.css";

export default function VideoPlayCheck() {
  const navigate = useNavigate();
  const { result = {} } = useResult() || {};
  const [videoUrl, setVideoUrl] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    console.log("[VideoPlayCheck] result =", result);

    if (result && result.video_file) {
      let videoPath = result.video_file.trim();
      let absoluteUrl = "";

      // ✅ 1️⃣ 이미 http로 시작하면 그대로 사용
      if (videoPath.startsWith("http")) {
        absoluteUrl = videoPath;

      // ✅ 2️⃣ /tmp 경로이지만 파일명이 존재할 경우 (업로드된 파일)
      } else if (videoPath.includes("/tmp/")) {
        const fileName = videoPath.split("/").pop();
        // FastAPI가 업로드 완료 후 실제 저장 폴더로 이동시킨 파일 접근
        absoluteUrl = `https://fersona.cloud/fersona/api/uploads/${fileName}`;
        console.log(`[VideoPlayCheck] tmp 경로 변환됨 → ${absoluteUrl}`);

      // ✅ 3️⃣ 서버 내부 경로 (/home/ubuntu/fersona/uploads)
      } else if (videoPath.includes("/uploads/")) {
        const fileName = videoPath.split("/").pop();
        absoluteUrl = `https://fersona.cloud/fersona/api/uploads/${fileName}`;

      // ✅ 4️⃣ 나머지 상대경로 처리
      } else {
        const fileName = videoPath.split("/").pop();
        absoluteUrl = `https://fersona.cloud/fersona/api/uploads/${fileName}`;
      }

      console.log("[VideoPlayCheck] 최종 videoUrl =", absoluteUrl);
      setVideoUrl(absoluteUrl);
      setError("");
    } else {
      setVideoUrl("");
      setError("⚠️ 영상 데이터가 존재하지 않습니다. 이전 화면에서 다시 시도해주세요.");
    }
  }, [result]);

  return (
    <div className={styles.videoPageContainer}>
      <div className={styles.videoHeader}>
        <h1>면접 영상 재생하기</h1>
        <button onClick={() => navigate(-1)} className={styles.backButton}>
          ← 이전 화면으로 돌아가기
        </button>
      </div>

      <div className={styles.videoPlaceholder}>
        {error && <p className={styles.errorText}>{error}</p>}

        {videoUrl && (
          <video
            src={videoUrl}
            controls
            preload="metadata"
            style={{
              width: "100%",
              maxHeight: "480px",
              background: "#111",
              borderRadius: "8px",
            }}
            onError={() =>
              setError(
                "⚠️ 영상 재생 중 오류가 발생했습니다. 파일이 삭제되었거나 접근할 수 없습니다."
              )
            }
          >
            <p>⚠️ 현재 브라우저는 video 태그를 지원하지 않습니다.</p>
          </video>
        )}
      </div>
    </div>
  );
}

