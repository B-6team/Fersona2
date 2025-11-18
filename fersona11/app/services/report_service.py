import time
import librosa
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import AnalysisResult, User


# =========================================
# ✅ numpy → JSON 변환 안전 처리 함수
# =========================================
def _to_plain_json(o: Any):
    """numpy, datetime 등 직렬화 불가 객체를 파이썬 기본형으로 변환"""
    try:
        import numpy as np
    except Exception:
        np = None

    if isinstance(o, dict):
        return {str(k): _to_plain_json(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_to_plain_json(v) for v in o]
    if np is not None:
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.ndarray,)):
            return [_to_plain_json(v) for v in o.tolist()]
    if isinstance(o, datetime):
        return o.isoformat()
    return o


# =========================================
# ✅ 점수 계산 헬퍼
# =========================================
def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    try:
        xf = float(x)
    except Exception:
        xf = 0.0
    return max(lo, min(hi, xf))


def _r1(x: float) -> float:
    return round(float(x), 1)


# =========================================
# ✅ 시선·표정 분석 + DB 저장 + 피드백 생성
# =========================================
def analyze_and_insert_with_feedback(
    db: Session,
    analysis_result: Dict,
    user_id: int | str = None,
    guest_token: str = None
) -> Dict:
    """
    시선/표정 분석 결과를 DB에 저장하고,
    - 시선: 중앙 응시율 + 깜빡임 분리
    - 각 항목별로 원인(cause) + 개선(correction) 메시지 생성
    + 프런트에서 바로 쓰는 *_score_value(소수 1자리) 포함
    """

    # ------------------------------------------
    # 0️⃣ user_id 문자열이면 users.id로 변환 (없으면 자동 생성)
    # ------------------------------------------
    if isinstance(user_id, str):
        user_obj = db.query(User).filter(User.username == user_id).first()
        if user_obj is None:
            try:
                new_user = User(username=user_id)
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user_obj = new_user
                print(f"[REPORT] 새 사용자 생성: username={user_obj.username}, id={user_obj.id}")
            except IntegrityError:
                db.rollback()
                user_obj = db.query(User).filter(User.username == user_id).first()
        user_id = user_obj.id if user_obj else None

    # ------------------------------------------
    # 1️⃣ 시선 분석: 중앙 응시율 + 깜빡임 분리
    # ------------------------------------------
    # 분석 결과에서 값 꺼내기 (없으면 기본값)
    gaze_center_ratio = analysis_result.get("gaze_center_ratio", None)
    gaze_center_score = analysis_result.get("gaze_score", None)
    blink_rate = analysis_result.get("blink_rate", None)
    blink_score = analysis_result.get("blink_score", None)

    # 안전한 float 변환 + 기본값
    if gaze_center_ratio is None:
        gaze_center_ratio = 0.0
    gaze_center_ratio = float(gaze_center_ratio)

    if gaze_center_score is None:
        # 중앙 응시율 비율을 점수로 환산하는 간단한 기본값 (0~1 → 0~100)
        gaze_center_score = gaze_center_ratio * 100.0
    gaze_center_score = _r1(_clamp(gaze_center_score))

    if blink_rate is None:
        blink_rate = 0.0
    blink_rate = float(blink_rate)

    if blink_score is None:
        # 정상 깜빡임 10~20회/분 기준으로 대략적인 점수
        blink_score = max(0.0, 100.0 - abs(blink_rate - 15.0) * 4.0)
    blink_score = _r1(_clamp(blink_score))

    # 중앙 응시 + 깜빡임을 합쳐서 "시선 종합 점수" 생성
    valid_scores = [s for s in [gaze_center_score, blink_score] if isinstance(s, (int, float,))]
    if valid_scores:
        gaze_total_score = _r1(sum(valid_scores) / len(valid_scores))
    else:
        gaze_total_score = 0.0

    # 🔹 중앙 응시율 피드백 (원인 + 개선)
    if gaze_center_ratio < 0.5:
        gaze_center_feedback = "시선이 자주 중앙에서 벗어납니다."
        gaze_center_cause = "카메라 렌즈보다 화면이나 주변을 보는 시간이 더 길어 보입니다."
        gaze_center_correction = "답변할 때는 화면 대신 카메라 렌즈를 바라보는 연습을 해보세요. 문장을 말할 때마다 렌즈를 한 번씩 확인하는 습관을 들이면 도움이 됩니다."
    elif 0.5 <= gaze_center_ratio < 0.7:
        gaze_center_feedback = "중앙 응시는 있지만, 시선이 다소 흔들립니다."
        gaze_center_cause = "중간중간 시선이 아래나 옆으로 자주 이동해 집중도가 약하게 느껴집니다."
        gaze_center_correction = "핵심 문장을 말할 때는 카메라를 바라보고, 생각이 필요할 때만 잠시 시선을 옮기는 식으로 패턴을 정해보세요."
    else:
        gaze_center_feedback = "카메라 중앙 응시가 전체적으로 잘 유지되고 있습니다."
        gaze_center_cause = "시선이 안정적으로 유지되어 신뢰감 있는 인상을 줍니다."
        gaze_center_correction = "현재처럼 중요한 포인트에서 카메라를 바라보는 습관을 유지하시면 좋습니다."

    # 🔹 깜빡임 피드백 (원인 + 개선)
    if blink_rate == 0.0 and analysis_result.get("blink_rate") is None:
        # 아예 깜빡임 분석이 안 들어온 경우
        blink_feedback = "깜빡임 데이터가 충분하지 않습니다."
        blink_cause = "조명/화질 문제 또는 얼굴 인식이 불안정했을 수 있습니다."
        blink_correction = "조명이 밝고 정면이 잘 보이는 환경에서 다시 촬영해보세요."
    elif blink_rate < 5:
        blink_feedback = "눈 깜빡임이 거의 없어 다소 긴장되어 보일 수 있습니다."
        blink_cause = "눈을 의식적으로 크게 뜨거나, 긴장으로 인해 깜빡임을 억제했을 가능성이 있습니다."
        blink_correction = "답변 중에도 자연스럽게 눈을 깜빡이는 연습을 해보세요. 말하기 전에 가볍게 눈을 감았다 뜨며 긴장을 풀어주는 것도 도움이 됩니다."
    elif blink_rate > 25:
        blink_feedback = "눈을 자주 깜빡이는 편입니다."
        blink_cause = "긴장 또는 안구 건조로 인해 깜빡임 빈도가 높게 나타난 것으로 보입니다."
        blink_correction = "답변 전에 눈을 잠시 감고 깊게 호흡해 긴장을 풀어보세요. 눈이 뻑뻑하다면 촬영 전 인공눈물을 사용하는 것도 방법입니다."
    else:
        blink_feedback = "깜빡임 빈도가 자연스러운 범위입니다."
        blink_cause = "시선 처리와 함께 눈 움직임도 안정적으로 유지되고 있습니다."
        blink_correction = "지금처럼 자연스럽게 눈을 깜빡이며 편안한 인상을 유지해보세요."

    # ------------------------------------------
    # 2️⃣ 표정 분석 → 점수 + 피드백/원인/교정
    # ------------------------------------------
    emotion = (analysis_result.get("dominant_emotion") or "neutral").lower()

    emotion_score_map = {
        "happy": 85.0,
        "neutral": 70.0,
        "surprise": 75.0,
        "sad": 55.0,
        "angry": 50.0,
        "fear": 55.0,
        "disgust": 50.0,
    }
    expression_score_value = _r1(_clamp(emotion_score_map.get(emotion, 70.0)))

    if emotion == "happy":
        expression_feedback = "긍정적인 표정으로 안정적인 인상을 주었습니다."
        expression_cause = "입꼬리와 눈 주변 근육이 자연스럽게 올라가 있어 친근한 느낌을 줍니다."
        expression_correction = "지금처럼 미소를 유지하되, 너무 과하지 않도록 질문의 분위기에 따라 진지함과 미소를 적절히 조절해보세요."
        expression_color = "green"
    elif emotion in ("sad", "angry", "disgust", "fear"):
        expression_feedback = "표정에서 다소 긴장감 또는 부정적인 인상이 감지됩니다."
        expression_cause = "눈썹, 입꼬리, 턱 근육이 굳어 있거나 아래로 처져 있어 불안/짜증/긴장으로 보일 수 있습니다."
        expression_correction = "답변 전 가볍게 얼굴 근육을 풀어주고, 입꼬리를 살짝 올리는 연습을 해보세요. 거울을 보며 편안한 표정을 만드는 것도 도움이 됩니다."
        expression_color = "red"
    else:
        expression_feedback = "무표정에 가까운 중립적인 표정을 유지했습니다."
        expression_cause = "큰 감정 변화는 없지만, 다소 딱딱하거나 긴장된 인상으로 느껴질 수 있습니다."
        expression_correction = "질문에 공감하는 미소나 고개 끄덕임을 조금만 추가해주면, 더 부드럽고 친절한 인상을 줄 수 있습니다."
        expression_color = "orange"

    # ------------------------------------------
    # 3️⃣ DB 저장 데이터 구성 (NOT NULL 보호)
    # ------------------------------------------
    video_path = analysis_result.get("video_path") or analysis_result.get("video_file") or "unknown_video.mp4"
    audio_path = analysis_result.get("audio_path") or analysis_result.get("audio_file") or "unknown_audio.wav"
    duration_sec = analysis_result.get("duration_sec", analysis_result.get("duration", 0.0))

    safe_result_data = _to_plain_json(analysis_result)

    record_data = {
        "user_id": user_id,
        "video_file": video_path,
        "audio_file": audio_path,
        "transcript": analysis_result.get("transcript", ""),
        "duration_sec": float(duration_sec) if duration_sec else 0.0,
        "result_data": safe_result_data,
        "created_at": datetime.now(),
    }

    try:
        record = AnalysisResult(**record_data)
        db.add(record)
        db.commit()
        db.refresh(record)
        print(f"[REPORT] DB 저장 완료 → id={record.id}, user_id={user_id}")
    except Exception as e:
        db.rollback()
        print(f"[REPORT ERROR] DB 저장 중 오류 발생: {e}")
        raise

    # ------------------------------------------
    # 4️⃣ 반환용 피드백 구조 (프론트에서 그대로 사용 가능)
    # ------------------------------------------
    feedback: Dict[str, Any] = {
        # 🔹 시선 종합 점수 + 세부 지표
        "gaze_total_score": gaze_total_score,
        "gaze_center_ratio": _r1(gaze_center_ratio * 100.0) if gaze_center_ratio else 0.0,  # %
        "gaze_center_score": gaze_center_score,
        "blink_rate": _r1(blink_rate),
        "blink_score": blink_score,

        # 중앙 응시율 피드백
        "gaze_center_feedback": gaze_center_feedback,
        "gaze_center_cause": gaze_center_cause,
        "gaze_center_correction": gaze_center_correction,

        # 깜빡임 피드백
        "blink_feedback": blink_feedback,
        "blink_cause": blink_cause,
        "blink_correction": blink_correction,

        # 표정 점수 + 피드백
        "expression_score_value": expression_score_value,
        "expression_feedback": expression_feedback,
        "expression_cause": expression_cause,
        "expression_correction": expression_correction,
        "expression_color": expression_color,
    }

    return {"record": record, "feedback": feedback}

