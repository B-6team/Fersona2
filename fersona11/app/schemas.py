from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

# ==========================
# USERS
# ==========================
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2: ORM 모델 변환 가능


# ==========================
# VIDEOS
# ==========================
class VideoBase(BaseModel):
    filename: str
    original_name: Optional[str] = None

class VideoCreate(VideoBase):
    owner_id: Optional[int] = None
    guest_token: Optional[str] = None

class VideoOut(VideoBase):
    id: int
    owner_id: Optional[int] = None
    guest_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================
# FEEDBACKS
# ==========================
class FeedbackBase(BaseModel):
    content: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    video_id: int
    user_id: Optional[int] = None
    guest_token: Optional[str] = None
    auto_saved: Optional[bool] = False

class FeedbackOut(FeedbackBase):
    id: int
    video_id: int
    user_id: Optional[int] = None
    guest_token: Optional[str] = None
    auto_saved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class FeedbackInput(BaseModel):
    video_id: int
    content: Optional[str] = None
    user_id: Optional[int] = None
    guest_token: Optional[str] = None
    auto_saved: Optional[bool] = False


# ==========================
# GAZE DATA
# ==========================
class GazeBase(BaseModel):
    result_json: Optional[str] = None

class GazeCreate(GazeBase):
    video_id: int
    feedback_id: Optional[int] = None
    raw_blob: Optional[bytes] = None

class GazeOut(GazeBase):
    id: int
    video_id: int
    feedback_id: Optional[int] = None
    raw_blob: Optional[bytes] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================
# GUEST SESSIONS
# ==========================
class GuestSessionBase(BaseModel):
    token: str

class GuestSessionCreate(GuestSessionBase):
    expires_at: datetime
    metadata_json: Optional[str] = None

class GuestSessionOut(GuestSessionBase):
    id: int
    created_at: datetime
    expires_at: datetime
    metadata_json: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================
# INTERVIEW RESULTS
# ==========================
class InterviewResultBase(BaseModel):
    video_file: Optional[str] = None
    audio_file: Optional[str] = None
    gaze_ratio: Optional[float] = None
    gaze_feedback: Optional[str] = None
    expression: Optional[str] = None
    gaze_color: Optional[str] = None
    speech_speed_wpm: Optional[int] = None
    syllable_count: Optional[int] = None
    speech_feedback_normal: Optional[str] = None
    speech_color_normal: Optional[str] = None
    speech_feedback_pressure: Optional[str] = None
    speech_color_pressure: Optional[str] = None
    transcript: Optional[str] = None
    speech_elapsed_time_sec: Optional[float] = None
    interview_date: Optional[datetime] = None

class InterviewResultCreate(InterviewResultBase):
    video_file: str
    audio_file: str
    gaze_ratio: float
    gaze_feedback: str
    expression: str
    gaze_color: str
    speech_speed_wpm: int
    syllable_count: int
    speech_feedback_normal: str
    speech_color_normal: str
    speech_feedback_pressure: str
    speech_color_pressure: str
    transcript: str
    speech_elapsed_time_sec: float

class InterviewResultOut(InterviewResultBase):
    id: int

    class Config:
        from_attributes = True


# ==========================
# REPORTS
# ==========================
class ReportBase(BaseModel):
    interview_id: int
    file_path: str

class ReportCreate(ReportBase):
    pass

class ReportOut(ReportBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
