from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# =====================================================
# ✅ 사용자(User) 테이블 모델
# =====================================================
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(512), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True)
    auth_provider = Column(String(50), default="local", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # 관계 설정 (1:N)
    analysis_results = relationship("AnalysisResult", back_populates="user")


# =====================================================
# ✅ 분석 결과(AnalysisResult) 테이블 모델
# =====================================================
class AnalysisResult(Base):
    __tablename__ = "analysis_result"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 업로드된 파일 정보
    video_file = Column(String(255), nullable=False)
    audio_file = Column(String(255), nullable=True)

    # 분석 결과
    transcript = Column(Text, nullable=True)
    duration_sec = Column(Float, nullable=True)
    result_data = Column(JSON, nullable=True)

    # 생성 일시
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # 관계 설정 (N:1)
    user = relationship("User", back_populates="analysis_results")

