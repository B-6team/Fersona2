from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import shutil
import uuid
import random
import threading

from app import models, schemas
from app.database import get_db
from app.utils.auth import get_current_user_optional
from app.questions import INTERVIEW_QUESTIONS

# ✅ 프론트 요청에 맞춰 prefix 변경
# (프론트: http://localhost:5000/fersona/api/upload-media)
router = APIRouter(prefix="", tags=["videos"])

UPLOAD_DIR = "uploaded_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ===========================
# 비회원 영상 자동 삭제 함수
# ===========================
def delete_guest_video(video_id: int, file_path: str, db_session_maker, delay_seconds: int = 3600):
    """delay_seconds 후에 비회원 영상 DB와 파일 삭제 (Thread 기반)"""
    def worker():
        try:
            threading.Event().wait(delay_seconds)  # non-blocking sleep
            db = db_session_maker()
            video = db.query(models.Video).filter(models.Video.id == video_id).first()
            if video:
                db.delete(video)
                db.commit()
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting guest video {video_id}: {e}")
        finally:
            db.close()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


# ===========================
# 면접 질문 랜덤 API
# ===========================
@router.get("/questions", response_model=list[str])
def get_interview_questions():
    return random.sample(INTERVIEW_QUESTIONS, 6)


# ===========================
# 🎥 영상 업로드 API (프론트엔드와 경로 일치)
# ===========================
@router.post("/upload-media", response_model=schemas.VideoOut)
def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_location = os.path.join(UPLOAD_DIR, unique_filename)

    # 파일 저장
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if current_user:
        video = models.Video(
            filename=file_location,
            original_name=file.filename,
            owner_id=current_user.id
        )
        db.add(video)
        db.commit()
        db.refresh(video)
    else:
        # 비회원 토큰 생성
        token = models.GuestSession.create_token()
        guest_session = models.GuestSession(
            token=token,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(guest_session)
        db.commit()
        db.refresh(guest_session)

        video = models.Video(
            filename=file_location,
            original_name=file.filename,
            guest_token=guest_session.token
        )
        db.add(video)
        db.commit()
        db.refresh(video)

        # ✅ 자동 삭제 스케줄 등록
        background_tasks.add_task(
            delete_guest_video,
            video_id=video.id,
            file_path=file_location,
            db_session_maker=db.get_bind().session_factory,
            delay_seconds=3600
        )

    return video


# ===========================
# 회원 업로드 영상 조회
# ===========================
@router.get("/videos", response_model=list[schemas.VideoOut])
def list_videos(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    videos = db.query(models.Video).filter(models.Video.owner_id == current_user.id).all()
    return videos


# ===========================
# 특정 영상 삭제
# ===========================
@router.delete("/videos/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if current_user:
        if video.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this video")
    else:
        raise HTTPException(status_code=401, detail="Guest videos auto-expire and cannot be manually deleted.")

    db.delete(video)
    db.commit()

    # 실제 파일 삭제
    if os.path.exists(video.filename):
        os.remove(video.filename)

    return {"message": "Video deleted successfully"}
