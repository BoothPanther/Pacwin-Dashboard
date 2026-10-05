from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ============================================================
# STATE
# ============================================================

class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False
    )


# ============================================================
# DISTRICT
# ============================================================

class District(Base):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    state_id: Mapped[int] = mapped_column(
        ForeignKey("states.id"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )


# ============================================================
# CONSTITUENCY / ASSEMBLY SEAT
# ============================================================

class Constituency(Base):
    __tablename__ = "constituencies"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    district_id: Mapped[int] = mapped_column(
        ForeignKey("districts.id"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    assembly_number: Mapped[int] = mapped_column(
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )


# ============================================================
# BOOTH
# ============================================================

class Booth(Base):
    __tablename__ = "booths"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    constituency_id: Mapped[int] = mapped_column(
        ForeignKey("constituencies.id"),
        nullable=False,
        index=True
    )

    booth_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    booth_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    polling_station: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True
    )

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    latitude: Mapped[float | None] = mapped_column(
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
        nullable=True
    )


# ============================================================
# PARTY
# ============================================================

class Party(Base):
    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False
    )

    abbreviation: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    color: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    symbol: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True
    )


# ============================================================
# ELECTION
# ============================================================

class Election(Base):
    __tablename__ = "elections"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    year: Mapped[int] = mapped_column(
        nullable=False
    )

    election_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )


# ============================================================
# CANDIDATE
# ============================================================

class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    constituency_id: Mapped[int] = mapped_column(
        ForeignKey("constituencies.id"),
        nullable=False,
        index=True
    )

    party_id: Mapped[int] = mapped_column(
        ForeignKey("parties.id"),
        nullable=False,
        index=True
    )


# ============================================================
# ELECTION RESULT
# ============================================================

class ElectionResult(Base):
    __tablename__ = "election_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    election_id: Mapped[int] = mapped_column(
        ForeignKey("elections.id"),
        nullable=False,
        index=True
    )

    constituency_id: Mapped[int] = mapped_column(
        ForeignKey("constituencies.id"),
        nullable=False,
        index=True
    )

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
        index=True
    )

    party_id: Mapped[int] = mapped_column(
        ForeignKey("parties.id"),
        nullable=False,
        index=True
    )

    votes: Mapped[int] = mapped_column(
        nullable=False
    )

    vote_share: Mapped[float] = mapped_column(
        nullable=False
    )

    position: Mapped[int] = mapped_column(
        nullable=False
    )

    is_winner: Mapped[bool] = mapped_column(
        nullable=False,
        default=False
    )


# ============================================================
# BOOTH ELECTION RESULT
# ============================================================

class BoothElectionResult(Base):
    __tablename__ = "booth_election_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    booth_id: Mapped[int] = mapped_column(
        ForeignKey("booths.id"),
        nullable=False,
        index=True
    )

    election_id: Mapped[int] = mapped_column(
        ForeignKey("elections.id"),
        nullable=False,
        index=True
    )

    party_id: Mapped[int] = mapped_column(
        ForeignKey("parties.id"),
        nullable=False,
        index=True
    )

    votes: Mapped[int] = mapped_column(
        nullable=False
    )


# ============================================================
# OLD / GENERAL REPORT
# ============================================================

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    seat_id: Mapped[int | None] = mapped_column(
        ForeignKey("constituencies.id"),
        nullable=True,
        index=True
    )

    report_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    file_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    election_year: Mapped[int | None] = mapped_column(
        nullable=True
    )

    processing_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )


# ============================================================
# CONSTITUENCY REPORT
# ============================================================

class ConstituencyReport(Base):
    __tablename__ = "constituency_reports"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    constituency_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "constituencies.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    report_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    original_file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    file_format: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    report_date: Mapped[str | None] = mapped_column(
        nullable=True
    )

    processing_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default="uploaded"
    )


# ============================================================
# REPORT SUMMARY
# ============================================================

class ReportSummary(Base):
    __tablename__ = "report_summaries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey(
            "constituency_reports.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    total_voters: Mapped[int | None] = mapped_column(
        nullable=True
    )

    male_percentage: Mapped[float | None] = mapped_column(
        nullable=True
    )

    female_percentage: Mapped[float | None] = mapped_column(
        nullable=True
    )

    rural_percentage: Mapped[float | None] = mapped_column(
        nullable=True
    )

    urban_percentage: Mapped[float | None] = mapped_column(
        nullable=True
    )

    religious_composition: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )


# ============================================================
# REPORT ELECTION RESULTS
# ============================================================

class ReportElectionResult(Base):
    __tablename__ = "report_election_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey(
            "constituency_reports.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    election_year: Mapped[int] = mapped_column(
        nullable=False
    )

    election_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    party_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    candidate_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    votes: Mapped[int | None] = mapped_column(
        nullable=True
    )

    vote_percentage: Mapped[float | None] = mapped_column(
        nullable=True
    )

    source_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )


# ============================================================
# REPORT PARTY ANALYSIS
# ============================================================

class ReportPartyAnalysis(Base):
    __tablename__ = "report_party_analysis"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey(
            "constituency_reports.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    party_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )


# ============================================================
# REPORT CANDIDATE ANALYSIS
# ============================================================

class ReportCandidateAnalysis(Base):
    __tablename__ = "report_candidate_analysis"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey(
            "constituency_reports.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    candidate_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    party_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )


# ============================================================
# REPORT AREA ANALYSIS
# ============================================================

class ReportAreaAnalysis(Base):
    __tablename__ = "report_area_analysis"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey(
            "constituency_reports.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    area_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )


# ============================================================
# REPORT ISSUES
# ============================================================

class ReportIssue(Base):
    __tablename__ = "report_issues"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey(
            "constituency_reports.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    issue_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    issue_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )