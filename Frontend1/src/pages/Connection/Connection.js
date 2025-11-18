import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // 추가
import { Camera, Mic, MicOff, VideoOff } from 'lucide-react';
import styles from './Connection.module.css';

function Connection() {
  const navigate = useNavigate(); // navigate 훅
  const [cameraConnected, setCameraConnected] = useState(false);
  const [micConnected, setMicConnected] = useState(false);
  const [showPermissionRequest, setShowPermissionRequest] = useState(false);
  const [stream, setStream] = useState(null);
  const videoRef = useRef(null);

  const requestPermission = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      setStream(mediaStream);
      setCameraConnected(true);
      setMicConnected(true);
      setShowPermissionRequest(false);
    } catch (error) {
      console.error('Permission denied:', error);
      setShowPermissionRequest(true);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
      setCameraConnected(false);
      setMicConnected(false);
      if (videoRef.current) videoRef.current.srcObject = null;
    }
  };

  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = stream;
  }, [stream]);

  useEffect(() => {
    return () => {
      if (stream) stream.getTracks().forEach((track) => track.stop());
    };
  }, [stream]);

  // 면접 시작 버튼 클릭 시 이동
  const handleStartInterview = () => {
    navigate('/interview'); // 이동할 경로
  };

  return (
    <div className={styles.appContainer}>
      <h1 className={styles.mainTitle}>
        곧 AI 면접이 시작됩니다. 그 전에 카메라와 마이크를 점검해 주세요.
      </h1>

      <div className={styles.mainContent}>
        <div className={styles.contentFlex}>
          <div className={styles.videoContainer}>
            <div className={styles.videoPlaceholder}>
              {cameraConnected ? (
                <video ref={videoRef} autoPlay muted className={styles.videoElement} />
              ) : (
                <div className={styles.videoOff}>
                  <VideoOff size={48} color="#666" />
                </div>
              )}
            </div>
          </div>

          <div className={styles.checklist}>
            <h2 className={styles.checklistTitle}>면접 전, 아래 항목을 확인해 주세요</h2>
            <div className={styles.checklistItems}>
              <p>• 조명이 충분히 밝은가요?</p>
              <p>• 얼굴과 상반신이 잘 보이나요?</p>
              <p>• 배경이 단정하고 방해 요소가 없나요?</p>
              <p>• 주변이 조용한 환경인가요?</p>
              <p><strong>• 준비가 끝났다면 녹화를 시작해 주세요.</strong></p>
            </div>
          </div>
        </div>
      </div>

      {/* 연결 버튼 / 면접 시작 버튼 */}
      {(!cameraConnected || !micConnected) ? (
        <button onClick={requestPermission} className={styles.connectBtn}>
          카메라 / 마이크 연결하기
        </button>
      ) : (
        <button onClick={handleStartInterview} className={styles.connectBtn}>
          면접 시작하기
        </button>
      )}

      <div className={styles.statusContainer}>
        <div className={styles.statusItem}>
          <Camera size={20} color={cameraConnected ? '#10B981' : '#EF4444'} />
          <span className={cameraConnected ? styles.statusConnected : styles.statusDisconnected}>
            {cameraConnected ? '카메라가 연결되었습니다' : '카메라가 연결되지 않았습니다'}
          </span>
        </div>
        <div className={styles.statusItem}>
          {micConnected ? <Mic size={20} color="#10B981" /> : <MicOff size={20} color="#EF4444" />}
          <span className={micConnected ? styles.statusConnected : styles.statusDisconnected}>
            {micConnected ? '마이크가 연결되었습니다' : '마이크가 연결되지 않았습니다'}
          </span>
        </div>
      </div>

      {showPermissionRequest && (
        <div className={styles.popupOverlay}>
          <div className={styles.popupContent}>
            <div className={styles.popupHeader}>
              <h3>Fersona Check에서 다음 권한을 요청합니다.</h3>
              <button onClick={() => setShowPermissionRequest(false)} className={styles.closeBtn}>✕</button>
            </div>
            <div className={styles.popupPermissions}>
              <div className={styles.permissionItem}>
                <Camera size={16} /><span>카메라 사용</span>
              </div>
              <div className={styles.permissionItem}>
                <Mic size={16} /><span>마이크 사용</span>
              </div>
            </div>
            <div className={styles.popupButtons}>
              <button onClick={requestPermission} className={`${styles.popupBtn} ${styles.primary}`}>사이트에 있는 동안 허용</button>
              <button onClick={requestPermission} className={`${styles.popupBtn} ${styles.secondary}`}>이번에만 허용</button>
              <button onClick={() => setShowPermissionRequest(false)} className={`${styles.popupBtn} ${styles.tertiary}`}>허용 안함</button>
            </div>
          </div>
        </div>
      )}

      {(cameraConnected || micConnected) && (
        <button onClick={stopCamera} className={styles.stopBtn}>연결 해제하기</button>
      )}
    </div>
  );
}

export default Connection;
