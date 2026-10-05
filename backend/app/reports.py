from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from database import engine
from models import Report
from seat_importer import import_seats


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"]
)


UPLOAD_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "uploads"
    / "reports"
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    with Session(engine) as session:
        yield session


ALLOWED_EXTENSIONS = {
    ".xlsx",
    ".xls",
    ".csv",
    ".pdf",
}


@router.post("/upload")
async def upload_report(
    file: UploadFile = File(...),
    report_name: str = Form(...),
    report_type: Literal[
        "seat_master",
        "election_result",
        "booth_result",
        "survey",
        "historical_election",
        "other",
    ] = Form(...),
    election_year: int | None = Form(None),
    seat_id: int | None = Form(None),
    db: Session = Depends(get_db),
):

    file_extension = Path(file.filename or "").suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        return {
            "status": "error",
            "message": "Unsupported file format."
        }

    unique_name = f"{uuid4().hex}{file_extension}"

    file_path = UPLOAD_DIR / unique_name

    file_content = await file.read()

    file_path.write_bytes(file_content)

    if seat_id == 0:
        seat_id = None

    if election_year == 0:
        election_year = None

    report = Report(
        seat_id=seat_id,
        report_name=report_name,
        report_type=report_type,
        file_name=file.filename,
        file_path=str(file_path),
        file_format=file_extension.replace(".", ""),
        election_year=election_year,
        processing_status="uploaded",
    )

    db.add(report)

    db.commit()

    db.refresh(report)

    if report_type == "seat_master":
        try:
            import_seats(str(file_path))
            report.processing_status = "processed"

        except Exception as error:
            report.processing_status = "failed"
            db.commit()

            return {
                "status": "error",
                "message": "Seat Master processing failed.",
                "error": str(error),
                "report_id": report.id,
            }

        db.commit()
        db.refresh(report)

    return {
        "status": "success",
        "message": "Report uploaded successfully.",
        "report": {
            "id": report.id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "file_name": report.file_name,
            "file_format": report.file_format,
            "processing_status": report.processing_status,
        },
    }