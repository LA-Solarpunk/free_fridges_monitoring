import os
import json
from typing import Optional, List
from pyairtable import Api
from pyairtable.formulas import AND, Field, IS_AFTER, DATEADD, CREATED_TIME, EQ, TODAY
from dataclasses import dataclass
import io
from io import StringIO
import csv

BASE_NAME = "app3C7ktuj4lyrQS6" 
READINGS_TABLE_NAME = "tbluQQWvULLlvZ2KY"
FRIDGE_TABLE_NAME = "tbl6qhf2XkHFyNKrg"

@dataclass
class Entry:
    temperature: float
    charge_status: float
    door_status: bool
    fridge_id: str

    def get_json_string(self):
        status = "Open" if self.door_status else "Closed"
        new_entry = {
            "Fridge": [self.fridge_id],
            "Temperature (°C)": self.temperature,
            "Charge Status (%)": self.charge_status,
            "Door Status": status,
        }
        return new_entry

def send_data_to_airtable(entry: Entry):
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(BASE_NAME, READINGS_TABLE_NAME)
    table.create(entry.get_json_string())

def get_fridge_ids():
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(BASE_NAME, FRIDGE_TABLE_NAME)
    return table.all(fields=["Fridge Name"])

def airtable_recent_rows_by_id_to_csv(
    id_value: str,
    id_field: str = "Fridge",
    days: int = 30,
    date_field: Optional[str] = None,  # if None, uses record Created Time
) -> str:
    """
    Fetch rows from Airtable created/dated within the last `days` where ANY of
    `id_fields` equals `id_value`. Returns a CSV string.

    - If `date_field` is None, filters by record CREATED_TIME().
      Otherwise compares the given date field (must be a date/datetime).
    - If `select_fields` is provided, only those columns are included in the CSV;
      otherwise all fields present in the returned records are included.
    """
    # Escape single quotes for Airtable formula string literals
    # (Airtable formulas use single quotes; escape with a backslash)
    safe_id = id_value.replace("'", "\\'")

    if date_field:
        date_clause = f"IS_AFTER({{{date_field}}}, DATEADD(TODAY(), -{days}, 'days'))"
    else:
        date_clause = f"IS_AFTER(CREATED_TIME(), DATEADD(TODAY(), -{days}, 'days'))"
    formula = date_clause

    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(BASE_NAME, READINGS_TABLE_NAME)
    records = table.all(formula=formula)

    # Client-side filter for the linked record ID, since filterByFormula
    # can’t reliably match a linked field by record ID directly.
    filtered = []
    for rec in records:
        f = rec.get("fields", {})
        linked_vals = f.get(id_field, [])
        # Linked record fields come back as a list of record ID strings
        if isinstance(linked_vals, list) and id_value in linked_vals:
            filtered.append(rec)

    # Build CSV
    # Determine headers: union of all returned field keys (or use provided `fields`)
    header_set = set()
    for rec in filtered:
        header_set.update(rec.get("fields", {}).keys())
    headers = sorted(header_set)

    # Always include the Airtable record ID as first column for traceability
    if "record_id" not in headers:
        headers = ["record_id"] + headers

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()

    for rec in filtered:
        row = {"record_id": rec.get("id")}
        # Flatten fields; for linked fields that are lists, join with commas
        for k, v in rec.get("fields", {}).items():
            if isinstance(v, list):
                # Join list into a comma-separated string
                row[k] = ", ".join(str(x) for x in v)
            else:
                row[k] = v
        writer.writerow(row)

    return output.getvalue()

def main():
    json_data = get_fridge_ids()
    print(json.dumps(json_data, indent=4))

if __name__ == "__main__":
    main()