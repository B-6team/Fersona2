import React from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Home.module.css";
import { FaLaptop } from "react-icons/fa";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.logoContainer}>
          <div className={styles.iconBox}>
            <FaLaptop className={styles.icon} />
          </div>
          <h1 className={styles.logoText}>Fersona check</h1>
        </div>
        <p className={styles.description}>
          카메라앞의 당신, AI가 분석해드립니다.
          <br />
          면접에 적합한 태도를 잡아보세요.
        </p>
        <button
          onClick={() => navigate("/connection")}
          className={styles.startButton}
        >
          지금 시작하기
        </button>
      </div>
    </div>
  );
}
