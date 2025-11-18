from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app import models, database

router = APIRouter()

@router.post("/guest/start")
def start_guest_session(db: Session = Depends(database.get_db)):
    token = models.GuestSession.create_token()
    expires_at = datetime.utcnow() + timedelta(hours=2)
    guest = models.GuestSession(token=token, expires_at=expires_at)
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return {"guest_token": guest.token, "expires_at": guest.expires_at}

@router.delete("/guest/end/{token}")
def end_guest_session(token: str, db: Session = Depends(database.get_db)):
    guest = db.query(models.GuestSession).filter(models.GuestSession.token == token).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest session not found")
    db.delete(guest)
    db.commit()
    return {"detail": "Guest session and all related data deleted"}
