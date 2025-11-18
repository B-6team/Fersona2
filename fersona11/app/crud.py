from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext

# 비밀번호 해싱용 bcrypt context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """비밀번호를 안전하게 해시"""
    return pwd_context.hash(password)


# ===== Users =====
def create_user(db: Session, user: schemas.UserCreate):
    """
    새로운 사용자 생성 (비밀번호 해시 적용)
    """
    hashed_pw = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int):
    """
    ID로 사용자 조회
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


# ===== Videos =====
def create_video(db: Session, video: schemas.VideoCreate):
    """
    새 비디오 레코드 생성
    """
    db_video = models.Video(**video.dict())
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video


def get_video(db: Session, video_id: int):
    """
    ID로 비디오 조회
    """
    return db.query(models.Video).filter(models.Video.id == video_id).first()


# ===== Feedbacks =====
def create_feedback(db: Session, feedback: schemas.FeedbackCreate):
    """
    인터뷰 피드백 데이터 저장
    """
    db_feedback = models.Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


# ===== GazeData =====
def create_gaze(db: Session, gaze: schemas.GazeDataCreate):
    """
    시선 데이터 저장
    """
    db_gaze = models.GazeData(**gaze.dict())
    db.add(db_gaze)
    db.commit()
    db.refresh(db_gaze)
    return db_gaze
