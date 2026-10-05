from pathlib import Path

import openpyxl
from sqlalchemy import text

from database import engine


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FILE_PATH = (
    BASE_DIR
    / "uploads"
    / "reports"
    / "Balachaur_Final_Booth.xlsx"
)

CONSTITUENCY_ID = 117


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    if value is None:
        return ""

    return str(value).strip()


def combine_unique(values):
    """
    Preserve all distinct non-empty Area values for a booth.
    If multiple Area values exist for the same Common_ID,
    combine them using ' + '.
    """

    result = []

    for value in values:
        value = clean_value(value)

        if value and value not in result:
            result.append(value)

    return " + ".join(result)


# ============================================================
# READ EXCEL
# ============================================================

if not FILE_PATH.exists():
    raise FileNotFoundError(
        f"Excel file not found:\n{FILE_PATH}"
    )

print(f"Reading Excel:\n{FILE_PATH}")

workbook = openpyxl.load_workbook(
    FILE_PATH,
    data_only=True
)

worksheet = workbook.active


headers = [
    clean_value(cell.value)
    for cell in worksheet[1]
]

header_map = {
    header: index
    for index, header in enumerate(headers)
}


required_columns = [
    "Common_ID",
    "Area",
]

for column in required_columns:
    if column not in header_map:
        raise ValueError(
            f"Required column missing: {column}"
        )


common_id_index = header_map["Common_ID"]
area_index = header_map["Area"]


# ============================================================
# COLLECT AREA BY COMMON_ID
# ============================================================

area_by_common_id = {}

total_rows = 0

for row in worksheet.iter_rows(
    min_row=2,
    values_only=True
):

    total_rows += 1

    common_id_raw = row[common_id_index]
    area_raw = row[area_index]

    if common_id_raw is None:
        continue

    try:
        common_id = int(common_id_raw)
    except (TypeError, ValueError):
        continue

    area = clean_value(area_raw)

    if common_id not in area_by_common_id:
        area_by_common_id[common_id] = []

    if area:
        area_by_common_id[common_id].append(area)


# ============================================================
# UPDATE DATABASE
# ============================================================

print()
print("Updating booth Area values...")

updated = 0
missing = 0

with engine.begin() as connection:

    booths = connection.execute(
        text("""
            SELECT
                id,
                booth_number,
                common_id
            FROM booths
            WHERE constituency_id = :constituency_id
            ORDER BY id
        """),
        {
            "constituency_id": CONSTITUENCY_ID
        }
    ).mappings().all()

    for booth in booths:

        common_id = booth["common_id"]

        if common_id not in area_by_common_id:
            missing += 1
            continue

        area = combine_unique(
            area_by_common_id[common_id]
        )

        connection.execute(
            text("""
                UPDATE booths
                SET area = :area
                WHERE id = :booth_id
            """),
            {
                "area": area,
                "booth_id": booth["id"],
            }
        )

        updated += 1


# ============================================================
# VERIFY
# ============================================================

with engine.connect() as connection:

    result = connection.execute(
        text("""
            SELECT
                COUNT(*) AS total_booths,
                COUNT(area) AS booths_with_area
            FROM booths
            WHERE constituency_id = :constituency_id
        """),
        {
            "constituency_id": CONSTITUENCY_ID
        }
    ).mappings().one()


print()
print("========================================")
print("AREA IMPORT COMPLETED")
print("========================================")
print(f"Excel rows          : {total_rows}")
print(f"Excel Common_IDs    : {len(area_by_common_id)}")
print(f"Booths updated      : {updated}")
print(f"Booths without area : {missing}")
print(f"DB total booths     : {result['total_booths']}")
print(f"DB booths with area : {result['booths_with_area']}")
print("========================================")