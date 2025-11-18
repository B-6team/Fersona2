import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './MainPage.module.css';

export default function MainPage() {
  const navigate = useNavigate();

  const playVideo = () => navigate('/interview-result/play-video');
  const redoInterview = () => navigate('/connection');

  return (
    <div className={styles.newMainContainer}>

      <main className={styles.newMainContent}>
        <div className={styles.buttonGroup}>
          <button className={styles.menuButton} onClick={playVideo}>
            <span className={styles.menuIcon}>▶️</span>
            면접 영상 재생하기
          </button>
          <button className={styles.menuButton} onClick={() => navigate('/interview-result/interview-report')}>
            <span className={styles.menuIcon}>📊</span>
            면접 결과 리포트 확인하기
          </button>
          <button className={styles.menuButton} onClick={() => navigate('/interview-result/feedback-report')}>
            <span className={styles.menuIcon}>🔊</span>
            발화 속도 피드백 확인하기
          </button>
          <button className={styles.menuButton} onClick={redoInterview}>
            <span className={styles.menuIcon}>🔄</span>
            면접 다시하기
          </button>
        </div>
      </main>
    </div>
  );
}