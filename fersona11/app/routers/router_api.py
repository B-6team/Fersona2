from fastapi import APIRouter, FastAPI, UploadFile, File, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

router = APIRouter(prefix="/interview", tags=["interview"])

# 저장 경로
REPORT_DIR = "reports"
VIDEO_DIR = "uploads"
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ==========================
# Request Body 모델
# ==========================
class ReportRequest(BaseModel):
    video_file: str
    gaze_ratio: float = 0.0
    speech_speed_wpm: float = 0.0
    expression: str = "neutral"

# ==========================
# PDF 생성
# ==========================
@router.post("/report/generate/")
def create_report(result: ReportRequest):
    output_path = os.path.join(REPORT_DIR, f"interview_report_{result.video_file}.pdf")
    # generate_interview_pdf(result.dict(), output_path)   # 실제 구현 함수 연결
    return {"pdf_file": output_path}

# ==========================
# PDF 다운로드
# ==========================
@router.get("/report/download/{filename}")
def download_report(filename: str):
    file_path = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    return FileResponse(file_path, media_type='application/pdf', filename=filename)

# ==========================
# 비디오 반환 (재생용)
# ==========================
@router.get("/video/{video_id}")
def get_video(video_id: str):
    # 실제 저장 포맷이 uploads/{video_id}_video.webm라고 가정
    video_path = os.path.join(VIDEO_DIR, f"{video_id}_video.webm")
    if not os.path.exists(video_path):
        return Response(status_code=404)
    return FileResponse(video_path, media_type="video/webm")

# ==========================
# 비디오 업로드 예시 (선택)
# ==========================
@router.post("/video/upload")
async def upload_video(file: UploadFile = File(...)):
    tag, ext = os.path.splitext(file.filename)
    save_path = os.path.join(VIDEO_DIR, f"{tag}_video{ext or '.webm'}")
    with open(save_path, "wb") as out_file:
        content = await file.read()
        out_file.write(content)
    return {"video_file": save_path}

# FastAPI에 router 등록
app = FastAPI()
app.include_router(router)
