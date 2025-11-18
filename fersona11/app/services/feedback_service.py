import numpy as np
from typing import Dict

# =========================
# 기준값 설정
# =========================
WPM_SLOW = 70       # 느린 발화 속도 기준
WPM_FAST = 100      # 빠른 발화 속도 기준
F0_STD_LOW = 15     # 억양 변화 기준 (표준편차)

# =========================
# 점수 계산 함수
# =========================
def calc_speech_score(wpm: float, syllables_total: int) -> float:
    """
    발화속도 점수 계산 (WPM + 음절수 반영)
    - 짧은 발화일수록 가중치 감소
    """
    syllable_factor = min(1.0, syllables_total / 120)

    if wpm <= 40:
        base = 50 + (wpm / 40) * 30
    elif 40 < wpm <= 70:
        base = 80 + (wpm - 40) * 0.5
    elif 70 < wpm <= 100:
        base = 100 - abs(85 - wpm) * 0.6
    elif 100 < wpm <= 130:
        base = 90 - (wpm - 100) * 0.6
    else:
        base = max(60.0, 80 - (wpm - 130) * 0.3)

    return round(base * syllable_factor, 1)


def calc_pitch_score(f0_std: float) -> float:
    """
    억양 점수 계산 (표준편차 기반)
    """
    if f0_std < 10:
        return 50.0
    elif 10 <= f0_std < 30:
        return 60.0 + (f0_std - 10)
    elif 30 <= f0_std <= 70:
        return 80.0 + (1 - abs(50 - f0_std) / 40) * 15
    elif 70 < f0_std <= 100:
        return 80.0 - (f0_std - 70) * 0.5
    else:
        return 65.0

# =========================
# 피드백 생성 함수
# =========================
def generate_feedback_with_segments(result: Dict) -> Dict:
    """
    Whisper 분석 결과 기반 피드백 생성
    - segment 단위 구간 피드백
    - 전체 평균 피드백
    - 점수 산출 포함
    """
    feedback = {"speech": [], "pitch": []}
    segments = result.get("segments", [])
    wpm_total = result.get("wpm_total", 0)
    syllables_total = result.get("syllables_total", 0)
    f0_std_total = result.get("f0_std_total", 0)

    # --------------------------
    # 1️⃣ 구간별 피드백 (KeyError 방지)
    # --------------------------
    for seg in segments:
        start = seg.get("start_time") or seg.get("start") or 0.0
        end = seg.get("end_time") or seg.get("end") or 0.0
        wpm = seg.get("seg_wpm", 0.0)
        f0_std = seg.get("f0_std", 0.0)

        # 발화속도 피드백
        if wpm < WPM_SLOW:
            feedback["speech"].append({
                "start_time": start,
                "end_time": end,
                "feedback": "발화 속도가 느린 구간입니다.",
                "cause": "호흡 템포가 일정하지 않거나 문장 사이 간격이 너무 길게 유지되었습니다.",
                "correction": "조금 더 일정한 리듬으로, 문장 사이의 멈춤을 줄이고 말해보세요."
            })
        elif wpm > WPM_FAST:
            feedback["speech"].append({
                "start_time": start,
                "end_time": end,
                "feedback": "발화 속도가 빠른 구간입니다.",
                "cause": "긴장하거나 내용 전달을 서두른 구간으로 보입니다.",
                "correction": "호흡을 늘리고, 문장 끝에서는 짧게 멈추며 안정감을 주도록 해보세요."
            })

        # 억양 피드백
        if f0_std < F0_STD_LOW:
            feedback["pitch"].append({
                "start_time": start,
                "end_time": end,
                "feedback": "억양 변화가 적은 구간입니다.",
                "cause": "톤이 일정하여 다소 단조롭게 들릴 수 있습니다.",
                "correction": "문장 중 강조할 단어에 힘을 주거나 피치를 살짝 높여보세요."
            })

    # --------------------------
    # 2️⃣ 전체 평균 기반 피드백 (세그먼트 없을 때)
    # --------------------------
    if not feedback["speech"]:
        if wpm_total < WPM_SLOW:
            feedback["speech"].append({
                "feedback": "전체적으로 발화 속도가 느립니다.",
                "cause": "발음은 명확하지만 템포가 느려 답변이 지루하게 들릴 수 있습니다.",
                "correction": "호흡 간격을 일정하게 유지하고, 템포를 10~15% 정도 높여보세요."
            })
        elif wpm_total > WPM_FAST:
            feedback["speech"].append({
                "feedback": "전체적으로 발화 속도가 빠릅니다.",
                "cause": "긴장감으로 인해 말을 서둘러서 표현력이 떨어졌습니다.",
                "correction": "호흡을 깊게 하고 문장 끝에서 짧은 멈춤을 넣으면 안정적인 인상을 줍니다."
            })
        else:
            feedback["speech"].append({
                "feedback": "발화 속도가 안정적입니다.",
                "cause": "속도 조절이 잘 되어 있으며, 전달력이 좋습니다.",
                "correction": "현재의 템포를 유지하면 좋습니다."
            })

    if not feedback["pitch"]:
        if f0_std_total < F0_STD_LOW:
            feedback["pitch"].append({
                "feedback": "전체적으로 억양 변화가 적습니다.",
                "cause": "감정이 덜 전달되어 단조롭게 들릴 수 있습니다.",
                "correction": "문장 끝부분에 살짝 피치 변화를 주면 자연스러운 억양이 됩니다."
            })
        else:
            feedback["pitch"].append({
                "feedback": "억양이 자연스럽습니다.",
                "cause": "문장 강약과 피치 변화가 균형 있게 조화를 이루고 있습니다.",
                "correction": "현재의 억양 패턴을 유지하세요."
            })

    # --------------------------
    # 3️⃣ 점수 계산 (음절 + WPM 반영)
    # --------------------------
    feedback.update({
        "speech_score_value": calc_speech_score(wpm_total, syllables_total),
        "pitch_score_value": round(calc_pitch_score(f0_std_total), 1)
    })

    return feedback

