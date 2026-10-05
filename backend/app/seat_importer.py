from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from database import engine
from models import State, District, Constituency


def read_seat_file(file_path: str) -> pd.DataFrame:
    path = Path(file_path)

    if path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)

    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)

    raise ValueError(
        "Unsupported file format. Use CSV or Excel."
    )


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""

    return " ".join(
        str(value).strip().split()
    ).lower()


def import_seats(file_path: str):
    df = read_seat_file(file_path)

    print("Columns found:")
    print(list(df.columns))

    required_columns = {
        "District Name",
        "AC No.",
        "AC Name",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    with Session(engine) as session:

        punjab = (
            session.query(State)
            .filter_by(code="PB")
            .first()
        )

        if not punjab:
            raise ValueError(
                "Punjab was not found in the database."
            )

        added = 0
        updated = 0
        skipped = 0

        districts = (
            session.query(District)
            .filter_by(state_id=punjab.id)
            .all()
        )

        district_lookup = {
            normalize_text(district.name): district
            for district in districts
        }

        # ---------------------------------------------------------
        # District name aliases
        # ---------------------------------------------------------
        # The Seat Master uses:
        # "Shaheed Bhagat Singh Nagar"
        #
        # The database contains:
        # "Shahid Bhagat Singh Nagar"
        #
        # This mapping allows both names to refer to the
        # same Punjab district without modifying the source CSV.
        district_aliases = {
            "shaheed bhagat singh nagar":
                "shahid bhagat singh nagar",
        }

        # The CSV may contain the district name only
        # on the first row of each district.
        # This variable remembers the latest district.
        current_district_name = ""

        for _, row in df.iterrows():

            # -----------------------------------------------------
            # Remember the current district
            # -----------------------------------------------------
            if not pd.isna(row["District Name"]):
                current_district_name = normalize_text(
                    row["District Name"]
                )

            district_name = current_district_name

            # -----------------------------------------------------
            # Apply district alias if required
            # -----------------------------------------------------
            district_name = district_aliases.get(
                district_name,
                district_name
            )

            ac_number = row["AC No."]
            ac_name = str(row["AC Name"]).strip()

            # -----------------------------------------------------
            # Validate row
            # -----------------------------------------------------
            if (
                not district_name
                or pd.isna(ac_number)
                or not ac_name
                or ac_name.lower() == "nan"
            ):
                skipped += 1
                continue

            # -----------------------------------------------------
            # Convert AC number to integer
            # -----------------------------------------------------
            try:
                assembly_number = int(ac_number)

            except (ValueError, TypeError):
                skipped += 1
                continue

            # -----------------------------------------------------
            # Find district
            # -----------------------------------------------------
            district = district_lookup.get(
                district_name
            )

            if not district:
                print(
                    f"District not found: "
                    f"{row['District Name']}"
                )

                skipped += 1
                continue

            # -----------------------------------------------------
            # Create unique Punjab constituency code
            # Example:
            # AC 4 -> PB-004
            # AC 46 -> PB-046
            # -----------------------------------------------------
            constituency_code = (
                f"PB-{assembly_number:03d}"
            )

            # -----------------------------------------------------
            # Check whether seat already exists
            # -----------------------------------------------------
            existing = (
                session.query(Constituency)
                .filter_by(
                    code=constituency_code
                )
                .first()
            )

            if existing:

                existing.name = ac_name
                existing.district_id = district.id
                existing.assembly_number = assembly_number

                updated += 1

            else:

                constituency = Constituency(
                    district_id=district.id,
                    name=ac_name,
                    code=constituency_code,
                    assembly_number=assembly_number,
                    category="UNKNOWN",
                )

                session.add(constituency)

                added += 1

        # ---------------------------------------------------------
        # Save changes
        # ---------------------------------------------------------
        session.commit()

        print()
        print("==============================")
        print("Seat import completed.")
        print("==============================")
        print(f"Added:   {added}")
        print(f"Updated: {updated}")
        print(f"Skipped: {skipped}")
        print("==============================")