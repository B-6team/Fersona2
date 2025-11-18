from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql
import json
import os
import mysql.connector
from app.config import settings  # ✅ config에서 불러오기

# =========================================
# ✅ SQLAlchemy 기본 설정
# =========================================
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =========================================
# ✅ SQLAlchemy 세션 의존성
# =========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================================
# ✅ MySQL Native 연결 함수 (for raw cursor)
# =========================================
def get_db_connection():
    """MySQL Connector로 커서 기반 연결"""
    try:
        conn = mysql.connector.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,  # ✅ 포트 추가
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
        )
        print("[DB] 연결 성공 ✅")
        return conn
    except Exception as e:
        print(f"[DB] 연결 실패 ❌: {e}")
        return None

# =========================================
# ✅ DB 초기화 함수 (analysis 테이블 자동 생성)
# =========================================
def init_db():
    """DB 초기화 및 ORM 테이블 자동 생성"""
    try:
        # ✅ SQLAlchemy ORM 테이블 생성
        Base.metadata.create_all(bind=engine)

        conn = get_db_connection()
        if not conn:
            raise Exception("DB 연결 실패")

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    video_path TEXT,
                    audio_path TEXT,
                    result_data JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("[DB] 테이블 확인 및 초기화 완료 ✅")

        return conn
    except Exception as e:
        print(f"[DB] init_db 실패 ❌: {e}")
        return None

