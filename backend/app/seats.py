from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import engine
from models import (
    Constituency,
    District,
    Report,
    ConstituencyReport,
    ReportSummary,
    ReportElectionResult,
    ReportPartyAnalysis,
    ReportCandidateAnalysis,
    ReportAreaAnalysis,
    ReportIssue,
)


router = APIRouter(
    prefix="/api/seats",
    tags=["Seats"]
)


# ============================================================
# DATABASE SESSION
# ============================================================

def get_db():
    with Session(engine) as session:
        yield session


# ============================================================
# GET ALL SEATS
# ============================================================

@router.get("")
def get_seats(db: Session = Depends(get_db)):
    seats = (
        db.query(
            Constituency.id,
            Constituency.assembly_number,
            Constituency.name,
            Constituency.code,
            Constituency.category,
            District.name.label("district_name")
        )
        .join(
            District,
            Constituency.district_id == District.id
        )
        .order_by(
            Constituency.assembly_number
        )
        .all()
    )

    return {
        "status": "success",
        "count": len(seats),
        "seats": [
            {
                "id": seat.id,
                "assembly_number": seat.assembly_number,
                "name": seat.name,
                "code": seat.code,
                "category": seat.category,
                "district": seat.district_name,
            }
            for seat in seats
        ]
    }


# ============================================================
# GET BASIC SEAT SUMMARY
# ============================================================

@router.get("/{seat_id}/summary")
def get_seat_summary(
    seat_id: int,
    db: Session = Depends(get_db)
):
    seat = (
        db.query(
            Constituency.id,
            Constituency.assembly_number,
            Constituency.name,
            Constituency.code,
            District.name.label("district_name")
        )
        .join(
            District,
            Constituency.district_id == District.id
        )
        .filter(
            Constituency.id == seat_id
        )
        .first()
    )

    if not seat:
        raise HTTPException(
            status_code=404,
            detail="Constituency not found."
        )

    report = (
        db.query(Report)
        .filter(
            Report.seat_id == seat_id
        )
        .order_by(
            Report.id.desc()
        )
        .first()
    )

    if not report:
        return {
            "status": "success",
            "seat": {
                "id": seat.id,
                "assembly_number": seat.assembly_number,
                "name": seat.name,
                "code": seat.code,
                "district": seat.district_name,
            },
            "report": None
        }

    return {
        "status": "success",
        "seat": {
            "id": seat.id,
            "assembly_number": seat.assembly_number,
            "name": seat.name,
            "code": seat.code,
            "district": seat.district_name,
        },
        "report": {
            "id": report.id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "file_name": report.file_name,
            "file_format": report.file_format,
            "election_year": report.election_year,
            "processing_status": report.processing_status,
            "summary": report.summary,
        }
    }


# ============================================================
# GET FULL SEAT REPORT
# ============================================================

@router.get("/{seat_id}/report")
def get_full_seat_report(
    seat_id: int,
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # 1. GET SEAT
    # --------------------------------------------------------

    seat = (
        db.query(
            Constituency.id,
            Constituency.assembly_number,
            Constituency.name,
            Constituency.code,
            Constituency.category,
            District.name.label("district_name")
        )
        .join(
            District,
            Constituency.district_id == District.id
        )
        .filter(
            Constituency.id == seat_id
        )
        .first()
    )

    if not seat:
        raise HTTPException(
            status_code=404,
            detail="Constituency not found."
        )

    # --------------------------------------------------------
    # 2. GET LATEST CONSTITUENCY REPORT
    # --------------------------------------------------------

    constituency_report = (
        db.query(ConstituencyReport)
        .filter(
            ConstituencyReport.constituency_id == seat_id
        )
        .order_by(
            ConstituencyReport.id.desc()
        )
        .first()
    )

    # --------------------------------------------------------
    # 3. IF NO REPORT EXISTS
    # --------------------------------------------------------

    if not constituency_report:
        return {
            "status": "success",
            "seat": {
                "id": seat.id,
                "assembly_number": seat.assembly_number,
                "name": seat.name,
                "code": seat.code,
                "category": seat.category,
                "district": seat.district_name,
            },
            "report": None,
            "summary": None,
            "election_results": [],
            "party_analysis": [],
            "candidate_analysis": [],
            "area_analysis": [],
            "issues": [],
        }

    report_id = constituency_report.id

    # --------------------------------------------------------
    # 4. GET REPORT SUMMARY
    # --------------------------------------------------------

    summary = (
        db.query(ReportSummary)
        .filter(
            ReportSummary.report_id == report_id
        )
        .first()
    )

    # --------------------------------------------------------
    # 5. GET ELECTION RESULTS
    # --------------------------------------------------------

    election_results = (
        db.query(ReportElectionResult)
        .filter(
            ReportElectionResult.report_id == report_id
        )
        .order_by(
            ReportElectionResult.election_year.desc(),
            ReportElectionResult.votes.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # 6. GET PARTY ANALYSIS
    # --------------------------------------------------------

    party_analysis = (
        db.query(ReportPartyAnalysis)
        .filter(
            ReportPartyAnalysis.report_id == report_id
        )
        .order_by(
            ReportPartyAnalysis.id
        )
        .all()
    )

    # --------------------------------------------------------
    # 7. GET CANDIDATE ANALYSIS
    # --------------------------------------------------------

    candidate_analysis = (
        db.query(ReportCandidateAnalysis)
        .filter(
            ReportCandidateAnalysis.report_id == report_id
        )
        .order_by(
            ReportCandidateAnalysis.id
        )
        .all()
    )

    # --------------------------------------------------------
    # 8. GET AREA ANALYSIS
    # --------------------------------------------------------

    area_analysis = (
        db.query(ReportAreaAnalysis)
        .filter(
            ReportAreaAnalysis.report_id == report_id
        )
        .order_by(
            ReportAreaAnalysis.id
        )
        .all()
    )

    # --------------------------------------------------------
    # 9. GET ISSUES
    # --------------------------------------------------------

    issues = (
        db.query(ReportIssue)
        .filter(
            ReportIssue.report_id == report_id
        )
        .order_by(
            ReportIssue.id
        )
        .all()
    )

    # --------------------------------------------------------
    # 10. RETURN COMPLETE REPORT
    # --------------------------------------------------------

    return {
        "status": "success",

        "seat": {
            "id": seat.id,
            "assembly_number": seat.assembly_number,
            "name": seat.name,
            "code": seat.code,
            "category": seat.category,
            "district": seat.district_name,
        },

        "report": {
            "id": constituency_report.id,
            "report_name": constituency_report.report_name,
            "original_file_name": constituency_report.original_file_name,
            "file_format": constituency_report.file_format,
            "processing_status": constituency_report.processing_status,
            "report_date": constituency_report.report_date,
        },

        "summary": (
            {
                "summary": summary.summary,
                "total_voters": summary.total_voters,

                "male_percentage": (
                    float(summary.male_percentage)
                    if summary.male_percentage is not None
                    else None
                ),

                "female_percentage": (
                    float(summary.female_percentage)
                    if summary.female_percentage is not None
                    else None
                ),

                "rural_percentage": (
                    float(summary.rural_percentage)
                    if summary.rural_percentage is not None
                    else None
                ),

                "urban_percentage": (
                    float(summary.urban_percentage)
                    if summary.urban_percentage is not None
                    else None
                ),

                "religious_composition": (
                    summary.religious_composition
                ),
            }
            if summary
            else None
        ),

        "election_results": [
            {
                "id": row.id,
                "election_year": row.election_year,
                "election_type": row.election_type,
                "party_name": row.party_name,
                "candidate_name": row.candidate_name,
                "votes": row.votes,

                "vote_percentage": (
                    float(row.vote_percentage)
                    if row.vote_percentage is not None
                    else None
                ),

                "source_note": row.source_note,
            }
            for row in election_results
        ],

        "party_analysis": [
            {
                "id": row.id,
                "party_name": row.party_name,
                "analysis": row.analysis,
            }
            for row in party_analysis
        ],

        "candidate_analysis": [
            {
                "id": row.id,
                "candidate_name": row.candidate_name,
                "party_name": row.party_name,
                "analysis": row.analysis,
            }
            for row in candidate_analysis
        ],

        "area_analysis": [
            {
                "id": row.id,
                "area_name": row.area_name,
                "analysis": row.analysis,
            }
            for row in area_analysis
        ],

        "issues": [
            {
                "id": row.id,
                "issue_title": row.issue_title,
                "issue_description": row.issue_description,
            }
            for row in issues
        ],
    }