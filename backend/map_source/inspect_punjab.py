import json

file_path = r"backend\map_source\punjab-ac.geojson"

with open(file_path, encoding="utf-8") as f:
    data = json.load(f)

print("Total:", len(data["features"]))

for feature in sorted(
    data["features"],
    key=lambda x: x["properties"]["ac_no"]
):
    p = feature["properties"]

    print(
        f"AC {p['ac_no']:03d} | "
        f"{p['ac_name']} | "
        f"{p['dist_name']} | "
        f"AC_ID {p['AC_ID']}"
    )
