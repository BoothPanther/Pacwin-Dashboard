from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import engine


BASE_DIR = Path(__file__).resolve().parents[2]
FILE_PATH = BASE_DIR / "uploads" / "reports" / "Balachaur_Final_Booth.xlsx"

BALACHAUR_AC_NUMBER = 48

WINNER_COLUMNS = {
    2012: "Winner_2012",
    2017: "Winner_2017",
    2022: "Winner_2022",
}

PARTY_ABBREVIATIONS = {
    "INC": "INC",
    "SAD": "SAD",
    "AAP": "AAP",
    "APP": "APP",
    "BJP": "BJP",
}


def clean_value(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def main():
    print("=" * 60)
    print("PACWIN - BALACHAUR BOOTH WINNER IMPORT")
    print("=" * 60)

    print()
    print("Reading file:")
    print(FILE_PATH)

    if not FILE_PATH.exists():
        raise FileNotFoundError(
            f"Excel file not found: {FILE_PATH}"
        )

    df = pd.read_excel(FILE_PATH)

    required_columns = [
        "Common_ID",
        "Winner_2012",
        "Winner_2017",
        "Winner_2022",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print()
    print(f"Total Excel rows: {len(df)}")

    unique_common_ids = (
        df["Common_ID"]
        .dropna()
        .unique()
        .tolist()
    )

    print(f"Unique Common_ID booths: {len(unique_common_ids)}")

    if len(unique_common_ids) != 197:
        raise ValueError(
            f"Expected 197 unique booths, found {len(unique_common_ids)}"
        )

    with engine.begin() as connection:

        # ---------------------------------------------------------
        # 1. Find Balachaur constituency
        # ---------------------------------------------------------
        constituency = connection.execute(
            text("""
                SELECT id, name
                FROM constituencies
                WHERE assembly_number = :assembly_number
            """),
            {
                "assembly_number": BALACHAUR_AC_NUMBER
            },
        ).fetchone()

        if not constituency:
            raise ValueError(
                f"Balachaur constituency not found for AC {BALACHAUR_AC_NUMBER}"
            )

        constituency_id = constituency.id

        print()
        print(
            f"Constituency found: {constituency.name} "
            f"(ID {constituency_id})"
        )

        # ---------------------------------------------------------
        # 2. Load database booths
        # ---------------------------------------------------------
        booth_rows = connection.execute(
            text("""
                SELECT id, common_id, booth_number
                FROM booths
                WHERE constituency_id = :constituency_id
                ORDER BY common_id
            """),
            {
                "constituency_id": constituency_id
            },
        ).fetchall()

        print(
            f"Database booths found: {len(booth_rows)}"
        )

        if len(booth_rows) != 197:
            raise ValueError(
                f"Expected 197 database booths, found {len(booth_rows)}"
            )

        booth_map = {
            row.common_id: row.id
            for row in booth_rows
        }

        # ---------------------------------------------------------
        # 3. Verify every Excel Common_ID exists in database
        # ---------------------------------------------------------
        missing_booths = [
            common_id
            for common_id in unique_common_ids
            if common_id not in booth_map
        ]

        if missing_booths:
            raise ValueError(
                f"Excel booths missing from database: {missing_booths}"
            )

        print("Booth mapping check: PASSED")

        # ---------------------------------------------------------
        # 4. Load elections
        # ---------------------------------------------------------
        election_rows = connection.execute(
            text("""
                SELECT id, year
                FROM elections
                WHERE year IN (2012, 2017, 2022)
            """)
        ).fetchall()

        election_map = {
            row.year: row.id
            for row in election_rows
        }

        required_years = {2012, 2017, 2022}

        if set(election_map.keys()) != required_years:
            raise ValueError(
                "Required elections 2012, 2017 and 2022 are not "
                "available in the database."
            )

        print("Election mapping check: PASSED")

        # ---------------------------------------------------------
        # 5. Load parties
        # ---------------------------------------------------------
        party_rows = connection.execute(
            text("""
                SELECT id, abbreviation
                FROM parties
                WHERE abbreviation IN ('INC', 'SAD', 'AAP', 'APP', 'BJP')
            """)
        ).fetchall()

        party_map = {
            row.abbreviation: row.id
            for row in party_rows
        }

        required_parties = {
            "INC",
            "SAD",
            "AAP",
            "APP",
            "BJP",
        }

        if set(party_map.keys()) != required_parties:
            raise ValueError(
                "Required parties INC, SAD, AAP, APP and BJP "
                "are not available in the database."
            )

        print("Party mapping check: PASSED")

        # ---------------------------------------------------------
        # 6. Validate all winner values before inserting anything
        # ---------------------------------------------------------
        print()
        print("Validating winner data...")

        for year, column in WINNER_COLUMNS.items():

            values = (
                df[column]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            invalid_values = [
                value
                for value in values
                if value not in PARTY_ABBREVIATIONS
            ]

            if invalid_values:
                raise ValueError(
                    f"Invalid party values in {column}: "
                    f"{invalid_values}"
                )

            print(
                f"{year}: {sorted(values)}"
            )

        print("Winner data validation: PASSED")

        # ---------------------------------------------------------
        # 7. Check existing booth election results
        # ---------------------------------------------------------
        existing_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM booth_election_results ber
                JOIN booths b
                    ON b.id = ber.booth_id
                WHERE b.constituency_id = :constituency_id
                  AND ber.election_id IN (
                      :election_2012,
                      :election_2017,
                      :election_2022
                  )
            """),
            {
                "constituency_id": constituency_id,
                "election_2012": election_map[2012],
                "election_2017": election_map[2017],
                "election_2022": election_map[2022],
            },
        ).scalar()

        print()
        print(
            f"Existing booth election records: {existing_count}"
        )

        if existing_count != 0:
            raise ValueError(
                "Booth election results already exist for "
                "Balachaur. Import stopped to prevent duplicates."
            )

        # ---------------------------------------------------------
        # 8. Insert winner records
        # ---------------------------------------------------------
        inserted_count = 0

        for _, row in df.drop_duplicates(
            subset=["Common_ID"]
        ).iterrows():

            common_id = row["Common_ID"]

            booth_id = booth_map.get(common_id)

            if booth_id is None:
                raise ValueError(
                    f"No database booth found for Common_ID {common_id}"
                )

            for year, column in WINNER_COLUMNS.items():

                winner = clean_value(row[column])

                if winner is None:
                    continue

                party_id = party_map[winner]
                election_id = election_map[year]

                connection.execute(
                    text("""
                        INSERT INTO booth_election_results
                        (
                            booth_id,
                            election_id,
                            party_id,
                            votes
                        )
                        VALUES
                        (
                            :booth_id,
                            :election_id,
                            :party_id,
                            0
                        )
                    """),
                    {
                        "booth_id": booth_id,
                        "election_id": election_id,
                        "party_id": party_id,
                    },
                )

                inserted_count += 1

        print()
        print("=" * 60)
        print("IMPORT COMPLETED")
        print("=" * 60)
        print()
        print(f"Unique booths processed : {len(unique_common_ids)}")
        print(f"Records inserted        : {inserted_count}")
        print()
        print("2024 records inserted   : 0")
        print("(No 2024 booth-level winner data exists in the Excel.)")
        print()
        print("SUCCESS")


if __name__ == "__main__":
    main()