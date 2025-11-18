from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
import shutil
import os
from typing import Optional

# 라우터 선언
router = APIRouter(prefix="/interview", tags=["Interview"])

# 업로드 경로 설정
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-media")
async def upload_media(
    video: UploadFile,
    audio: Optional[UploadFile] = None,
    user_id: Optional[int] = Form(None),
    guest_token: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # 파일 저장
        video_path = os.path.join(UPLOAD_DIR, video.filename)
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        audio_path = None
        if audio:
            audio_path = os.path.join(UPLOAD_DIR, audio.filename)
            with open(audio_path, "wb") as buffer:
                shutil.copyfileobj(audio.file, buffer)

        # 분석 후 RDS 저장
        result = analyze_and_insert_interview(
            db=db,
            video_path=video_path,
            audio_path=audio_path,
            user_id=user_id,
            guest_token=guest_token
        )

        return {"status": "success", "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload or analyze media: {e}")

