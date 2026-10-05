from database import engine
from models import State, District
from sqlalchemy.orm import Session


PUNJAB_DISTRICTS = [
    ("049", "Amritsar"),
    ("054", "Barnala"),
    ("046", "Bathinda"),
    ("045", "Faridkot"),
    ("040", "Fatehgarh Sahib"),
    ("648", "Fazilka"),
    ("043", "Ferozepur"),
    ("035", "Gurdaspur"),
    ("038", "Hoshiarpur"),
    ("037", "Jalandhar"),
    ("036", "Kapurthala"),
    ("041", "Ludhiana"),
    ("781", "Malerkotla"),
    ("047", "Mansa"),
    ("042", "Moga"),
    ("647", "Pathankot"),
    ("048", "Patiala"),
    ("051", "Rupnagar"),
    ("052", "Sahibzada Ajit Singh Nagar"),
    ("053", "Sangrur"),
    ("039", "Shahid Bhagat Singh Nagar"),
    ("044", "Sri Muktsar Sahib"),
    ("050", "Tarn Taran"),
]


def seed_districts():
    with Session(engine) as session:
        punjab = session.query(State).filter_by(code="PB").first()

        if not punjab:
            print("Punjab not found. Run seed_punjab.py first.")
            return

        added = 0

        for code, name in PUNJAB_DISTRICTS:
            existing = (
                session.query(District)
                .filter_by(state_id=punjab.id, code=code)
                .first()
            )

            if not existing:
                district = District(
                    state_id=punjab.id,
                    name=name,
                    code=code,
                )
                session.add(district)
                added += 1

        session.commit()

        print(f"{added} Punjab districts added successfully.")


if __name__ == "__main__":
    seed_districts()