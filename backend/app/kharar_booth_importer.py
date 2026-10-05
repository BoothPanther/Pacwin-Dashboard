
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import text

from database import engine

BASE_DIR = Path(__file__).resolve().parents[2]
FILE_PATH = BASE_DIR / "uploads" / "reports" / "Kharar_BJP_DashboardSheet.csv"

AC_NUMBER = 52
REQUIRED_COLUMNS = [
    "Common_ID",
    "Booth_number",
    "Booth_Name",
    "Polling_station_building",
    "Area",
    "Year",
    "Party",
    "Vote",
    "Winner_2022",
    "Winner_2017",
    "Winner_2012",
]

# The source file stores Ranjit Singh Gill as a candidate name in winner
# columns. For the Pacwin booth table, the required display is the party.
# Ranjit Singh Gill contested Kharar on the SAD ticket.
WINNER_PARTY_MAP = {
    "Ranjit Singh Gill": "SAD",
    "INC": "INC",
    "AAP": "AAP",
    "BJP": "BJP",
    "BSP": "BSP",
}

def clean(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value in {"", "NA", "N/A", "NONE", "NULL"}:
        return None
    return value

def winner_to_party(value):
    value = clean(value)
    if value is None:
        return None
    return WINNER_PARTY_MAP.get(value, value)

def main():
    replace_existing = "--replace" in sys.argv

    if not FILE_PATH.exists():
        raise FileNotFoundError(
            f"Source file not found:\n{FILE_PATH}\n\n"
            "Copy Kharar_BJP_DashboardSheet.csv into "
            "E:\\Pacwin\\uploads\\reports\\ first."
        )

    df = pd.read_csv(FILE_PATH)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["Common_ID"] = pd.to_numeric(df["Common_ID"], errors="coerce")
    df = df.dropna(subset=["Common_ID"]).copy()
    df["Common_ID"] = df["Common_ID"].astype(int)

    print(f"Source rows       : {len(df)}")
    print(f"Unique Common_ID  : {df['Common_ID'].nunique()}")
    print(f"Years             : {sorted(df['Year'].dropna().unique().tolist())}")

    with engine.begin() as conn:
        constituency = conn.execute(
            text("""
                SELECT id, name, assembly_number
                FROM constituencies
                WHERE assembly_number = :ac_number
            """),
            {"ac_number": AC_NUMBER},
        ).mappings().first()

        if not constituency:
            raise RuntimeError(f"AC {AC_NUMBER} was not found in constituencies.")

        constituency_id = constituency["id"]
        print(
            f"Constituency      : {constituency['name']} "
            f"(ID {constituency_id}, AC {constituency['assembly_number']})"
        )

        existing = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM booths
                WHERE constituency_id = :constituency_id
            """),
            {"constituency_id": constituency_id},
        ).scalar_one()

        if existing and not replace_existing:
            raise RuntimeError(
                f"{existing} booths already exist for AC {AC_NUMBER}. "
                "Nothing was changed. Run with --replace only if you "
                "intentionally want to replace the existing Kharar booth data."
            )

        if replace_existing and existing:
            conn.execute(
                text("""
                    DELETE FROM booth_election_results
                    WHERE booth_id IN (
                        SELECT id FROM booths
                        WHERE constituency_id = :constituency_id
                    )
                """),
                {"constituency_id": constituency_id},
            )
            conn.execute(
                text("""
                    DELETE FROM booths
                    WHERE constituency_id = :constituency_id
                """),
                {"constituency_id": constituency_id},
            )
            print(f"Removed existing Kharar booths: {existing}")

        # Party IDs already used by Pacwin.
        party_rows = conn.execute(
            text("SELECT id, abbreviation FROM parties")
        ).mappings().all()
        party_ids = {row["abbreviation"]: row["id"] for row in party_rows}

        required_parties = {"INC", "AAP", "BJP", "BSP", "SAD"}
        for abbreviation in required_parties:
            if abbreviation not in party_ids:
                conn.execute(
                    text("""
                        INSERT INTO parties (name, abbreviation)
                        VALUES (:name, :abbreviation)
                    """),
                    {
                        "name": abbreviation,
                        "abbreviation": abbreviation,
                    },
                )

        party_rows = conn.execute(
            text("SELECT id, abbreviation FROM parties")
        ).mappings().all()
        party_ids = {row["abbreviation"]: row["id"] for row in party_rows}

        booth_groups = df.groupby("Common_ID", sort=True)

        inserted_booths = 0
        inserted_winners = 0

        # Create one DB booth per Common_ID.
        for common_id, group in booth_groups:
            first = group.iloc[0]

            booth_number = clean(first["Booth_number"])
            booth_name = clean(first["Booth_Name"])
            polling_station = clean(first["Polling_station_building"])
            area = clean(first["Area"])

            result = conn.execute(
                text("""
                    INSERT INTO booths (
                        constituency_id,
                        booth_number,
                        booth_name,
                        polling_station,
                        address,
                        common_id
                    )
                    VALUES (
                        :constituency_id,
                        :booth_number,
                        :booth_name,
                        :polling_station,
                        :area,
                        :common_id
                    )
                    RETURNING id
                """),
                {
                    "constituency_id": constituency_id,
                    "booth_number": booth_number,
                    "booth_name": booth_name,
                    "polling_station": polling_station,
                    "area": area,
                    "common_id": int(common_id),
                },
            )

            booth_id = result.scalar_one()
            inserted_booths += 1

            # One winner record per available election year.
            for year, winner_column in [
                (2012, "Winner_2012"),
                (2017, "Winner_2017"),
                (2022, "Winner_2022"),
            ]:
                winner_values = group[winner_column].dropna().astype(str).str.strip()
                winner_values = winner_values[winner_values != ""]
                winner_values = winner_values[winner_values.str.upper() != "NA"]

                if winner_values.empty:
                    continue

                winner_party = winner_to_party(winner_values.iloc[0])
                if winner_party not in party_ids:
                    print(
                        f"WARNING: unmapped winner '{winner_party}' "
                        f"for Common_ID {common_id}, year {year}; skipped."
                    )
                    continue

                election_id = conn.execute(
                    text("""
                        SELECT id
                        FROM elections
                        WHERE year = :year
                        ORDER BY id
                        LIMIT 1
                    """),
                    {"year": year},
                ).scalar()

                if not election_id:
                    raise RuntimeError(f"Election row for year {year} not found.")

                conn.execute(
                    text("""
                        INSERT INTO booth_election_results (
                            booth_id,
                            election_id,
                            party_id,
                            votes
                        )
                        VALUES (
                            :booth_id,
                            :election_id,
                            :party_id,
                            0
                        )
                    """),
                    {
                        "booth_id": booth_id,
                        "election_id": election_id,
                        "party_id": party_ids[winner_party],
                    },
                )
                inserted_winners += 1

    print("")
    print("IMPORT COMPLETED")
    print(f"Unique booths in CSV : {df['Common_ID'].nunique()}")
    print(f"Inserted booths       : {inserted_booths}")
    print(f"Winner records        : {inserted_winners}")
    print("2024 winner records   : 0 (not present in source file)")
    print("SUCCESS: Kharar AC 52 import finished.")

if __name__ == "__main__":
    main()
