from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.FeedbackOut)
def create_feedback(feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    """
    피드백 생성
    - 로그인한 유저면 user_id 사용
    - 비회원이면 guest_token 사용
    """
    if not feedback.user_id and not feedback.guest_token:
        raise HTTPException(status_code=400, detail="user_id or guest_token required")

    fb = models.Feedback(
        video_id=feedback.video_id,
        user_id=feedback.user_id,
        guest_token=feedback.guest_token,
        content=feedback.content,
        auto_saved=feedback.auto_saved
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb  # 스키마 FeedbackOut에서 id, content 등 반환

@router.get("/video/{video_id}", response_model=list[schemas.FeedbackOut])
def list_feedbacks(video_id: int, db: Session = Depends(get_db)):
    """
    특정 영상에 대한 피드백 리스트 조회
    """
    feedbacks = db.query(models.Feedback).filter(models.Feedback.video_id == video_id).all()
    return feedbacks
