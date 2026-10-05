from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import engine


router = APIRouter(
    prefix="/api/historical-winners",
    tags=["Historical Winners"],
)


@router.get("/constituency/{constituency_id}")
def get_historical_winners(constituency_id: int):

    query = text("""
        SELECT
            id,
            election_year,
            candidate_name,
            party_name,
            votes_received,
            vote_share,
            community,
            profession,
            photo_url
        FROM historical_winner_candidates
        WHERE constituency_id = :constituency_id
        ORDER BY election_year DESC
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {
                "constituency_id": constituency_id
            },
        ).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No historical winner data found for this constituency.",
        )

    return {
        "status": "success",
        "constituency_id": constituency_id,
        "winners": [dict(row) for row in rows],
    }