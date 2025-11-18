from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas

router = APIRouter(prefix="/gaze", tags=["gaze"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.GazeOut)
def create_gaze(gaze: schemas.GazeCreate, db: Session = Depends(get_db)):
    """
    시선 데이터 생성
    """
    gd = models.GazeData(
        video_id=gaze.video_id,
        feedback_id=gaze.feedback_id,
        result_json=gaze.result,  # 모델 컬럼명 맞춤
        raw_blob=gaze.raw_blob
    )
    db.add(gd)
    db.commit()
    db.refresh(gd)
    return gd

@router.get("/video/{video_id}", response_model=list[schemas.GazeOut])
def list_gaze(video_id: int, db: Session = Depends(get_db)):
    """
    특정 영상에 대한 시선 데이터 조회
    """
    entries = db.query(models.GazeData).filter(models.GazeData.video_id == video_id).all()
    return entries
