from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import engine


router = APIRouter(
    prefix="/api/booths",
    tags=["Booth-wise Analysis"],
)


@router.get("/constituency/{constituency_id}")
def get_booths_by_constituency(constituency_id: int):

    query = text("""
        SELECT
            b.id,
            b.booth_number,
            b.booth_name,
            b.polling_station,
            b.address AS area,

            e.year AS election_year,
            p.abbreviation AS winner_party

        FROM booths b

        LEFT JOIN booth_election_results ber
            ON ber.booth_id = b.id

        LEFT JOIN elections e
            ON e.id = ber.election_id

        LEFT JOIN parties p
            ON p.id = ber.party_id

        WHERE b.constituency_id = :constituency_id

        ORDER BY
            CASE
                WHEN NULLIF(
                    REGEXP_REPLACE(
                        b.booth_number,
                        '[^0-9]',
                        '',
                        'g'
                    ),
                    ''
                ) IS NULL
                THEN 999999
                ELSE CAST(
                    REGEXP_REPLACE(
                        b.booth_number,
                        '[^0-9]',
                        '',
                        'g'
                    ) AS INTEGER
                )
            END,
            b.id,
            e.year
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"constituency_id": constituency_id},
        ).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No booths found for this constituency."
        )

    booths_map = {}
    available_years = set()

    for row in rows:

        booth_id = row["id"]

        if booth_id not in booths_map:
            booths_map[booth_id] = {
                "id": row["id"],
                "booth_number": row["booth_number"],
                "booth_name": row["booth_name"],
                "polling_station": row["polling_station"],
                "area": row["area"],
                "winner_by_year": {},
            }

        year = row["election_year"]
        winner = row["winner_party"]

        if year is not None and winner:
            year = int(year)

            booths_map[booth_id]["winner_by_year"][str(year)] = winner

            available_years.add(year)

    booths = list(booths_map.values())

    return {
        "status": "success",
        "constituency_id": constituency_id,
        "total_booths": len(booths),
        "available_years": sorted(available_years),
        "booths": booths,
    }