# app/routers/reports.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import get_db

# ===========================
# FastAPI 라우터 정의
# ===========================
router = APIRouter(prefix="/reports", tags=["reports"])

# ===========================
# 전체 리포트 조회
# ===========================
@router.get("/", response_model=List[schemas.ReportOut])
def list_reports(db: Session = Depends(get_db)):
    return db.query(models.Report).all()

# ===========================
# 특정 리포트 조회
# ===========================
@router.get("/{report_id}", response_model=schemas.ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report

# ===========================
# 리포트 생성
# ===========================
@router.post("/", response_model=schemas.ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(report: schemas.ReportBase, db: Session = Depends(get_db)):
    db_report = models.Report(**report.dict())
    try:
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return db_report

# ===========================
# 리포트 삭제
# ===========================
@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    try:
        db.delete(report)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return {"message": "Report deleted successfully"}
