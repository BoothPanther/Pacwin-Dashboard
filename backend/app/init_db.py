from database import engine
from models import (
    Base,
    State,
    District,
    Constituency,
    Booth,
    Party,
    Election,
    Candidate,
    ElectionResult,
    BoothElectionResult,
    Report,
    ConstituencyReport,
    ReportSummary,
    ReportElectionResult,
    ReportPartyAnalysis,
    ReportCandidateAnalysis,
    ReportAreaAnalysis,
    ReportIssue,
)


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Pacwin database tables created successfully.")


if __name__ == "__main__":
    create_tables()