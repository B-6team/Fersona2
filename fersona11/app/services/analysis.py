import os
import cv2
import numpy as np
import librosa
import whisper
import mediapipe as mp
import subprocess
import soundfile as sf
import re
from typing import Dict, Any

# ----------------------------------------
# 전역 모델 캐시
# ----------------------------------------
whisper_model = None
face_mesh = None


# ----------------------------------------
# Whisper 및 FaceMesh 초기화
# ----------------------------------------
def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        model_name = os.getenv("WHISPER_MODEL", "base").strip()
        try:
            print(f"[INFO] Whisper 모델 로드 중... (model={model_name})")
            whisper_model = whisper.load_model(model_name)
        except Exception as e:
            print(f"[WARN] 모델 '{model_name}' 로드 실패 → tiny로 폴백: {e}")
            whisper_model = whisper.load_model("tiny")
        print("[INFO] Whisper 모델 로드 완료")
    return whisper_model


def get_face_mesh():
    global face_mesh
    if face_mesh is None:
        print("[INFO] Mediapipe FaceMesh 초기화 중...")
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        print("[INFO] FaceMesh 초기화 완료")
    return face_mesh


# ----------------------------------------
# 비디오 → 오디오 추출
# ----------------------------------------
def extract_audio_from_video(video_path: str, audio_path: str):
    """ffmpeg로 영상에서 오디오 추출"""
    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ac", "1", "-ar", "16000",
        "-af", "volume=+10dB",
        "-acodec", "pcm_s16le",
        audio_path,
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ----------------------------------------
# 시선 + 표정 분석
# ----------------------------------------
def analyze_video_features(video_path: str, max_frames: int = 150, frame_interval: int = 5) -> Dict[str, Any]:
    cap = cv2.VideoCapture(video_path)
    gaze_list, mouth_ratio_list = [], []
    processed, frame_idx = 0, 0

    if not cap.isOpened():
        return {
            "gaze_feedback": "영상 인식 실패",
            "gaze_correction": "조명이 충분한 환경에서 다시 촬영해주세요.",
            "expression_feedback": "분석 불가",
            "expression_correction": "카메라를 정면으로 바라보세요.",
            "gaze_score_value": 0.0,
            "expression_score_value": 0.0,
        }

    face_mesh_local = get_face_mesh()

    while processed < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval != 0:
            frame_idx += 1
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh_local.process(frame_rgb)
        multi = getattr(results, "multi_face_landmarks", [])

        if multi:
            face = multi[0].landmark
            left_eye = np.array([[face[i].x, face[i].y] for i in [33, 133]])
            right_eye = np.array([[face[i].x, face[i].y] for i in [362, 263]])
            mouth = np.array([[face[i].x, face[i].y] for i in [13, 14]])

            gaze = np.mean([left_eye.mean(axis=0), right_eye.mean(axis=0)], axis=0)
            gaze_list.append(gaze)
            mouth_ratio_list.append(np.linalg.norm(mouth[1] - mouth[0]))

        processed += 1
        frame_idx += 1

    cap.release()

    gaze_x = float(np.mean([g[0] for g in gaze_list])) if gaze_list else 0.5
    mouth_mean = float(np.mean(mouth_ratio_list)) if mouth_ratio_list else 0.0

    penalty = abs(gaze_x - 0.5) * 200.0
    gaze_score_value = round(max(0.0, min(100.0, 100.0 - penalty)), 1)

    if mouth_mean > 0.0:
        expression_raw = (mouth_mean / 0.03) * 100.0
        expression_score_value = round(max(0.0, min(100.0, expression_raw)), 1)
    else:
        expression_score_value = 50.0

    if gaze_x < 0.45 or gaze_x > 0.55:
        gaze_feedback = "시선이 불안정합니다."
        gaze_correction = "카메라 중앙을 바라보세요."
    else:
        gaze_feedback = "시선이 안정적입니다."
        gaze_correction = "현재 시선 처리 방식이 좋습니다."

    if mouth_mean < 0.015:
        expression_feedback = "무표정이 감지되었습니다."
        expression_correction = "입꼬리를 살짝 올려 부드러운 표정을 만들어보세요."
    else:
        expression_feedback = "표정이 자연스럽습니다."
        expression_correction = "현재의 표정을 유지해 주세요."

    return {
        "gaze_feedback": gaze_feedback,
        "gaze_correction": gaze_correction,
        "expression_feedback": expression_feedback,
        "expression_correction": expression_correction,
        "gaze_score_value": gaze_score_value,
        "expression_score_value": expression_score_value,
    }


# ----------------------------------------
# 발화 분석 (Whisper + WPM + 억양)
# ----------------------------------------
def count_korean_syllables(text: str) -> int:
    """한글 음절 수 세기"""
    return len(re.findall(r"[가-힣]", text))


def calc_speech_score(wpm: float) -> float:
    if wpm <= 40.0:
        return 50.0 + (wpm / 40.0) * 30.0
    elif 40.0 < wpm <= 60.0:
        return 80.0 + (wpm - 40.0) * 0.5
    elif 60.0 < wpm <= 100.0:
        return 90.0 + (1.0 - abs(80.0 - wpm) / 40.0) * 10.0
    elif 100.0 < wpm <= 130.0:
        return 95.0 - (wpm - 100.0) * 0.5
    else:
        return max(60.0, 80.0 - (wpm - 130.0) * 0.4)


def calc_pitch_score(f0_std: float) -> float:
    if f0_std < 10.0:
        return 30.0
    elif 10.0 <= f0_std < 30.0:
        return 50.0 + (f0_std - 10.0)
    elif 30.0 <= f0_std <= 70.0:
        return 80.0 + (1.0 - abs(50.0 - f0_std) / 40.0) * 15.0
    elif 70.0 < f0_std <= 100.0:
        return 80.0 - (f0_std - 70.0) * 0.6
    else:
        return 60.0


def analyze_speech(audio_path: str) -> Dict[str, Any]:
    """Whisper를 이용한 발화 + 억양 분석"""
    try:
        y, sr = librosa.load(audio_path, sr=16000)
        rms = float(np.mean(librosa.feature.rms(y=y)))
        duration = float(librosa.get_duration(y=y, sr=sr))

        if rms < 0.01:
            gain = 0.02 / max(rms, 1e-6)
            y = y * gain
            print(f"[INFO] 볼륨이 낮아 {gain:.1f}배 증폭 적용 (rms={rms:.4f})")

        norm_path = "/tmp/normalized_input.wav"
        sf.write(norm_path, y, sr)

        model = get_whisper_model()
        print(f"[ANALYSIS] Whisper 분석 중... (audio={norm_path})")

        result = model.transcribe(norm_path, fp16=False, language="ko")
        text = result.get("text", "").strip()
        segments = result.get("segments", [])

        if segments:
            speech_time = float(sum(seg.get("end", 0.0) - seg.get("start", 0.0) for seg in segments))
        else:
            speech_time = duration

        if speech_time < duration:
            speech_time = duration

        syllables_total = count_korean_syllables(text)
        wpm_total = (syllables_total / speech_time) * 60.0 if speech_time > 0 else 0.0

        try:
            f0, _, _ = librosa.pyin(
                y,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
            )
            valid = f0[~np.isnan(f0)] if f0 is not None else []
            if valid.size > 0:
                f0_mean = float(np.mean(valid))
                f0_std = float(np.std(valid))
            else:
                f0_mean = 0.0
                f0_std = 0.0
        except Exception as e:
            print(f"[WARN] F0 추출 실패: {e}")
            f0_mean = 0.0
            f0_std = 0.0

        speech_score_value = calc_speech_score(wpm_total)
        pitch_score_value = calc_pitch_score(f0_std)

        feedback = {"speech": [], "pitch": []}

        if syllables_total == 0:
            feedback["speech"].append("음성이 감지되지 않아 발화속도를 분석할 수 없습니다.")
        elif wpm_total < 80:
            feedback["speech"].append("발화 속도가 약간 느립니다.")
        elif wpm_total > 130:
            feedback["speech"].append("발화 속도가 빠른 편입니다.")
        else:
            feedback["speech"].append("발화 속도가 안정적입니다.")

        if f0_std < 20:
            feedback["pitch"].append("억양이 다소 단조롭습니다.")
        elif f0_std > 60:
            feedback["pitch"].append("억양 변화가 다소 큽니다.")
        else:
            feedback["pitch"].append("억양이 안정적입니다.")

        return {
            "text": text,
            "duration": round(duration, 2),
            "speech_time": round(speech_time, 2),
            "syllables_total": int(syllables_total),
            "wpm_total": round(wpm_total, 2),
            "f0_mean_total": round(f0_mean, 2),
            "f0_std_total": round(f0_std, 2),
            "speech_score_value": round(speech_score_value, 1),
            "pitch_score_value": round(pitch_score_value, 1),
            "feedback": feedback,
            "segments": segments,
        }

    except Exception as e:
        print(f"[ERROR] 음성 분석 실패: {e}")
        return {
            "text": "",
            "duration": 0.0,
            "speech_time": 0.0,
            "syllables_total": 0,
            "wpm_total": 0.0,
            "f0_mean_total": 0.0,
            "f0_std_total": 0.0,
            "speech_score_value": 0.0,
            "pitch_score_value": 0.0,
            "feedback": {"speech": ["분석 실패"], "pitch": ["분석 실패"]},
            "segments": [],
        }


# ----------------------------------------
# 프론트에서 바로 쓰는 통합 분석 결과
# ----------------------------------------
def run_full_analysis(video_path: str, user_id: str | None = None) -> Dict[str, Any]:
    """영상 1개에 대해 오디오 추출 → 시선/표정 → 발화/억양 분석"""
    audio_path = f"/tmp/{os.path.basename(video_path)}_audio.wav"
    extract_audio_from_video(video_path, audio_path)

    video_report = analyze_video_features(video_path)
    whisper_result = analyze_speech(audio_path)

    return {
        "audio_file": audio_path,
        "video_file": video_path,
        "user_id": user_id,
        "report": {
            "gaze_feedback": video_report["gaze_feedback"],
            "gaze_correction": video_report["gaze_correction"],
            "expression_feedback": video_report["expression_feedback"],
            "expression_correction": video_report["expression_correction"],
            "gaze_score_value": video_report["gaze_score_value"],
            "expression_score_value": video_report["expression_score_value"],
        },
        "whisper": whisper_result,
    }

