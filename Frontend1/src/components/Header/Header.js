import React from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Header.module.css";
import { FaLaptop, FaUser } from "react-icons/fa";

export default function Header({ isLoggedIn, toggleLogin }) {
  const navigate = useNavigate();

  return (
    <header className={styles.header}>
      <div className={styles.logoContainer} onClick={() => navigate("/")}>
        <FaLaptop className={styles.icon} />
        <h1 className={styles.logoText}>Fersona check</h1>
      </div>
      <div className={styles.loginContainer}>
        <FaUser className={styles.userIcon} />
        <button onClick={toggleLogin} className={styles.loginBtn}>
          {isLoggedIn ? "USER1" : "LOGIN"}
        </button>
      </div>
    </header>
  );
}
