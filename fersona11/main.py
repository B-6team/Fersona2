import os
import json
import tempfile
import subprocess
import traceback
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import sessionmaker
from app.database import engine, init_db, get_db_connection
from app.services.analysis import analyze_speech, analyze_video_features
from app.services.feedback_service import generate_feedback_with_segments
from app.services.report_service import analyze_and_insert_with_feedback
from app.models import User

# =========================================
# ✅ 업로드 디렉토리 설정
# =========================================
UPLOAD_DIR = "/home/ubuntu/fersona/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

# ✅ 정적 파일 서빙 (React와 Nginx의 /fersona/api/uploads 경로 일치)
app.mount("/fersona/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# =========================================
# ✅ DB 저장 함수
# =========================================
def save_analysis_to_db(conn, user_id, video_path, audio_path, result_data):
    """분석 결과 DB 저장"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO analysis (user_id, video_path, audio_path, timestamp, result_data)
                VALUES (%s, %s, %s, NOW(), %s)
            """, (user_id, video_path, audio_path, json.dumps(result_data)))
            conn.commit()
            print("[DB] 데이터 저장 완료 ✅")
    except Exception as e:
        print(f"[DB] 저장 실패: {e}")
    finally:
        if conn:
            conn.close()


# =========================================
# ✅ 비디오 처리 함수 (오디오 추출)
# =========================================
def process_video(video_path: str):
    """비디오에서 오디오 추출"""
    try:
        tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            tmp_audio
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[FFMPEG ERROR] {result.stderr}")
            return None

        print(f"[FFMPEG] 오디오 추출 완료 → {tmp_audio}")
        return tmp_audio
    except Exception as e:
        print(f"[ERROR] ffmpeg 추출 실패: {e}")
        return None


# =========================================
# ✅ 업로드 처리 엔드포인트 (기본)
# =========================================
@app.post("/fersona/api/upload")
async def upload_media(
    user_id: str = Form(...),
    video: UploadFile = Form(...),
):
    try:
        print(f"[UPLOAD] 요청 수신 user_id={user_id}, file={video.filename}")

        # 1️⃣ 비디오 저장
        save_path = os.path.join(UPLOAD_DIR, video.filename)
        with open(save_path, "wb") as f:
            f.write(await video.read())
        print(f"[UPLOAD] 비디오 저장 완료 → {save_path}")

        # 2️⃣ 오디오 추출
        temp_audio = process_video(save_path)
        if not temp_audio:
            raise HTTPException(status_code=500, detail="오디오 추출 실패")

        # 3️⃣ Whisper + 비디오 분석
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        print("[ANALYSIS] Whisper 음성 분석 시작...")
        whisper_result = analyze_speech(temp_audio)

        print("[ANALYSIS] Whisper 세그먼트 피드백 생성...")
        whisper_feedback = generate_feedback_with_segments(whisper_result)
        whisper_result["feedback"] = whisper_feedback

        print("[ANALYSIS] 비디오(시선/표정) 분석 시작...")
        report_result = analyze_video_features(save_path)

        # ✅ 사용자 정보 확인/생성
        user_obj = db.query(User).filter(User.username == user_id).first()
        if not user_obj:
            user_obj = User(username=user_id)
            db.add(user_obj)
            db.commit()
            db.refresh(user_obj)
            print(f"[USER] 새 사용자 생성: username={user_id}, id={user_obj.id}")

        # ✅ 결과 통합 및 DB 반영
        analyze_and_insert_with_feedback(
            db=db,
            analysis_result=whisper_result,
            user_id=user_obj.id
        )

        # ✅ 결과 JSON 통합
        result_data = {
            "user_id": user_id,
            "video_file": f"/fersona/api/uploads/{video.filename}",
            "audio_file": temp_audio,
            "report": report_result,
            "whisper": whisper_result
        }

        # ✅ DB 저장
        conn = init_db()
        save_analysis_to_db(conn, user_id, save_path, temp_audio, result_data)

        print("[UPLOAD] 전체 프로세스 완료 ✅")
        return {"result": result_data}

    except Exception as e:
        print("[ERROR] 업로드 중 예외 발생:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# ✅ alias: /upload → /fersona/api/upload
# =========================================
@app.post("/upload")
async def upload_alias(
    user_id: str = Form(...),
    video: UploadFile = Form(...),
):
    """호환용 alias 경로 (/upload → /fersona/api/upload)"""
    print("[ALIAS] /upload 경로로 요청 → /fersona/api/upload 처리")
    return await upload_media(user_id=user_id, video=video)


# =========================================
# ✅ 결과 조회 엔드포인트
# =========================================
@app.get("/fersona/api/result/{user_id}")
def get_analysis_result(user_id: str):
    """특정 user_id의 최근 분석 결과 조회"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="DB 연결 실패")

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, video_path, audio_path, timestamp, result_data
                FROM analysis
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
            """, (user_id,))
            result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail=f"{user_id} 결과 없음")

        parsed = {}
        if result.get("result_data"):
            try:
                parsed = json.loads(result["result_data"])
            except Exception:
                parsed = {}

        response = {
            "result": {
                "id": result.get("id"),
                "user_id": result.get("user_id"),
                "video_file": parsed.get("video_file", ""),
                "audio_file": parsed.get("audio_file", ""),
                "report": parsed.get("report", {}),
                "whisper": parsed.get("whisper", {}),
                "timestamp": result.get("timestamp"),
            }
        }

        print(f"[RESULT] 조회 성공 user_id={user_id}")
        return response

    except Exception as e:
        print(f"[ERROR] 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


# =========================================
# ✅ 실행부
# =========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

