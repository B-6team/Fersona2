from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ----------------------------
    # ✅ 데이터베이스 설정 (타입 힌트 추가)
    # ----------------------------
    DB_HOST: str = "fersona.cdg2mym0m1gr.eu-north-1.rds.amazonaws.com"
    DB_PORT: int = 3306
    DB_USER: str = "admin"
    DB_PASSWORD: str = "비밀번호"
    DB_NAME: str = "fersona_db"

    # ----------------------------
    # ✅ JWT 및 토큰 관련 설정
    # ----------------------------
    SECRET_KEY: str = "defaultsecretkey"           # 기본값, .env가 있으면 덮어씀
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60          # 기본값, 필요 시 .env에서 덮어쓰기

    class Config:
        # 루트 디렉토리의 .env 파일 자동 로드
        env_file = ".env"
        env_file_encoding = "utf-8"

# ✅ 전역 설정 객체 생성
settings = Settings()

