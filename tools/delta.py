import json
import hashlib
import pandas as pd


def create_record_key(row, key_columns):
    key_parts = []

    for column in key_columns:
        value = row.get(column)
        key_parts.append(str(value).strip())

    return "_".join(key_parts)


def create_record_hash(record):
    record_json = json.dumps(
        record,
        sort_keys=True,
        default=str
    )

    return hashlib.sha256(record_json.encode("utf-8")).hexdigest()


def check_delta(
    df,
    previous_hashes=None,
    key_columns=None
):
    if previous_hashes is None:
        previous_hashes = {}

    if key_columns is None:
        key_columns = ["country", "deal_id"]

    records_to_create = []
    records_to_update = []
    records_to_skip = []
    current_hashes = {}

    for _, row in df.iterrows():
        record = row.to_dict()

        record_key = create_record_key(row, key_columns)
        record_hash = create_record_hash(record)

        current_hashes[record_key] = record_hash

        old_hash = previous_hashes.get(record_key)

        if old_hash is None:
            records_to_create.append(record)

        elif old_hash != record_hash:
            records_to_update.append(record)

        else:
            records_to_skip.append(record)

    result = {
        "to_create": records_to_create,
        "to_update": records_to_update,
        "to_skip": records_to_skip,
        "current_hashes": current_hashes
    }

    return result


if __name__ == "__main__":
    data = {
        "country": ["India", "USA", "Germany"],
        "deal_id": ["501", "1001", "DE-801"],
        "company_name": ["Tata Solutions", "Acme Corp", "Siemens AG"],
        "deal_value_usd": [30000.0, 125000.0, 102600.0],
        "sales_stage": ["proposal", "qualification", "qualification"],
        "expected_close_date": ["2026-10-15", "2026-09-15", "2026-10-15"],
        "source_file": [
            "crm_export_india.csv",
            "crm_export_us.csv",
            "crm_export_germany.xlsx"
        ]
    }

    df = pd.DataFrame(data)

    old_record_same = df.iloc[0].to_dict()
    old_record_changed = df.iloc[1].to_dict()
    old_record_changed["deal_value_usd"] = 100000.0

    previous_hashes = {
        "India_501": create_record_hash(old_record_same),
        "USA_1001": create_record_hash(old_record_changed)
    }

    result = check_delta(
        df,
        previous_hashes=previous_hashes,
        key_columns=["country", "deal_id"]
    )

    print("To create:")
    for record in result["to_create"]:
        print(record)

    print("\nTo update:")
    for record in result["to_update"]:
        print(record)

    print("\nTo skip:")
    for record in result["to_skip"]:
        print(record)

    print("\nCurrent hashes:")
    print(result["current_hashes"])