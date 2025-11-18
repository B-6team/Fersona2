from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import Token
from app.utils import create_access_token
import requests

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/tokeninfo"

@router.post("/google", response_model=Token)
def google_login(token: str, db: Session = Depends(get_db)):
    """
    구글 OAuth 로그인
    클라이언트에서 받은 ID 토큰을 검증하고, 유저 생성/로그인 처리
    """
    # 1) 구글 토큰 검증
    res = requests.get(GOOGLE_TOKEN_URL, params={"id_token": token})
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    
    google_data = res.json()
    google_id = google_data["sub"]      # 구글 고유 사용자 ID
    email = google_data.get("email")
    name = google_data.get("name", email.split("@")[0])

    # 2) DB에서 기존 사용자 확인
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        # 신규 사용자면 DB에 저장
        user = User(
            username=name,
            email=email,
            google_id=google_id,
            auth_provider="google",
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3) JWT 토큰 발급
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
