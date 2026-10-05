from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import engine


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR.parent / "uploads" / "reports" / "Balachaur_Final_Booth.xlsx"

BALACHAUR_AC_NUMBER = 48


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def first_non_empty(series):
    for value in series:
        cleaned = clean_value(value)
        if cleaned is not None:
            return cleaned

    return None


# ============================================================
# MAIN IMPORT
# ============================================================

def main():

    print("=" * 60)
    print("PACWIN - BALACHAUR BOOTH IMPORT")
    print("=" * 60)

    if not FILE_PATH.exists():
        raise FileNotFoundError(
            f"\nExcel file not found:\n{FILE_PATH}\n\n"
            "Please place Balachaur Final Booth (1).xlsx "
            "inside backend/uploads/reports/"
        )

    print(f"\nReading file:")
    print(FILE_PATH)

    df = pd.read_excel(FILE_PATH, engine="openpyxl")

    print(f"\nTotal Excel rows: {len(df)}")

    required_columns = [
        "Common_ID",
        "Booth_number",
        "BOOTH NAME ",
        "Polling_station_building",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # --------------------------------------------------------
    # GROUP BY Common_ID
    # --------------------------------------------------------

    grouped = []

    for common_id, group in df.groupby(
        "Common_ID",
        dropna=True
    ):

        booth_number = first_non_empty(
            group["Booth_number"]
        )

        booth_name = first_non_empty(
            group["BOOTH NAME "]
        )

        polling_station = first_non_empty(
            group["Polling_station_building"]
        )

        grouped.append(
            {
                "common_id": int(common_id),
                "booth_number": booth_number,
                "booth_name": booth_name,
                "polling_station": polling_station,
            }
        )

    print(f"Unique Common_ID booths: {len(grouped)}")

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    with engine.begin() as connection:

        # Find Balachaur
        constituency = connection.execute(
            text(
                """
                SELECT id, assembly_number, name
FROM constituencies
WHERE assembly_number = :ac_number
                """
            ),
            {
                "ac_number": BALACHAUR_AC_NUMBER
            },
        ).mappings().first()

        if not constituency:
            raise RuntimeError(
                f"Constituency AC {BALACHAUR_AC_NUMBER} "
                "was not found in the database."
            )

        constituency_id = constituency["id"]

        print(
            f"\nConstituency found:"
            f" {constituency['name']}"
            f" (ID {constituency_id})"
        )

        # Safety check
        existing_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM booths
                WHERE constituency_id = :constituency_id
                """
            ),
            {
                "constituency_id": constituency_id
            },
        ).scalar_one()

        print(
            f"Existing booths for this constituency: "
            f"{existing_count}"
        )

        if existing_count > 0:
            raise RuntimeError(
                "Booths already exist for Balachaur. "
                "Import stopped to prevent duplicates."
            )

        # ----------------------------------------------------
        # INSERT BOOTHS
        # ----------------------------------------------------

        inserted = 0

        for booth in grouped:

            connection.execute(
                text(
                    """
                    INSERT INTO booths (
                        constituency_id,
                        booth_number,
                        booth_name,
                        polling_station,
                        common_id
                    )
                    VALUES (
                        :constituency_id,
                        :booth_number,
                        :booth_name,
                        :polling_station,
                        :common_id
                    )
                    """
                ),
                {
                    "constituency_id": constituency_id,
                    "booth_number": booth["booth_number"],
                    "booth_name": booth["booth_name"],
                    "polling_station": booth["polling_station"],
                    "common_id": booth["common_id"],
                },
            )

            inserted += 1

    # --------------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------------

    with engine.connect() as connection:

        db_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM booths
                WHERE constituency_id = :constituency_id
                """
            ),
            {
                "constituency_id": constituency_id
            },
        ).scalar_one()

        distinct_common_id_count = connection.execute(
            text(
                """
                SELECT COUNT(DISTINCT common_id)
                FROM booths
                WHERE constituency_id = :constituency_id
                """
            ),
            {
                "constituency_id": constituency_id
            },
        ).scalar_one()

    print("\n" + "=" * 60)
    print("IMPORT COMPLETED")
    print("=" * 60)

    print(f"Excel unique booths : {len(grouped)}")
    print(f"Inserted booths      : {inserted}")
    print(f"Database booth count : {db_count}")
    print(f"Unique Common_ID     : {distinct_common_id_count}")

    if (
        len(grouped)
        == inserted
        == db_count
        == distinct_common_id_count
    ):
        print("\nSUCCESS: Booth count matches exactly.")
    else:
        print(
            "\nWARNING: Booth counts do not match. "
            "Do not continue."
        )


if __name__ == "__main__":
    main()