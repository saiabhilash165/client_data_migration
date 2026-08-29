import re
import json
import pandas as pd
from datetime import datetime


def create_issue(issue_type, row, field_name, current_value, reason, suggested_value=None):
    return {
        "issue_type": issue_type,
        "source_file": row.get("source_file"),
        "row_number": row.get("source_row_number"),
        "field_name": field_name,
        "current_value": current_value,
        "suggested_value": suggested_value,
        "reason": reason,
        "status": "open"
    }


def is_empty(value):
    return pd.isna(value) or str(value).strip() == ""


def is_valid_email(value):
    if is_empty(value):
        return True

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(email_pattern, str(value).strip()) is not None


def is_valid_date(value):
    if is_empty(value):
        return False

    try:
        datetime.strptime(str(value).strip(), "%Y-%m-%d")
        return True
    except Exception:
        return False


def validate_type(value, expected_type):
    if expected_type == "string":
        return isinstance(value, str)

    if expected_type == "number":
        try:
            float(value)
            return True
        except Exception:
            return False

    return True


def validate_json_schema(df, target_schema):
    issues = []

    fields = target_schema.get("fields", {})

    for index, row in df.iterrows():
        for field_name, rules in fields.items():
            required = rules.get("required", False)
            expected_type = rules.get("type")
            expected_format = rules.get("format")
            allowed_values = rules.get("allowed_values")

            current_value = row.get(field_name)

            if required and is_empty(current_value):
                issues.append(
                    create_issue(
                        issue_type="missing_required_field",
                        row=row,
                        field_name=field_name,
                        current_value=current_value,
                        reason=f"{field_name} is required but missing."
                    )
                )
                continue

            if is_empty(current_value):
                continue

            if expected_type and not validate_type(current_value, expected_type):
                issues.append(
                    create_issue(
                        issue_type="invalid_type",
                        row=row,
                        field_name=field_name,
                        current_value=current_value,
                        reason=f"{field_name} should be of type {expected_type}."
                    )
                )
                continue

            if expected_format == "email" and not is_valid_email(current_value):
                issues.append(
                    create_issue(
                        issue_type="invalid_email",
                        row=row,
                        field_name=field_name,
                        current_value=current_value,
                        reason=f"{field_name} should be a valid email."
                    )
                )
                continue

            if expected_format == "date" and not is_valid_date(current_value):
                issues.append(
                    create_issue(
                        issue_type="invalid_date_format",
                        row=row,
                        field_name=field_name,
                        current_value=current_value,
                        reason=f"{field_name} should be in YYYY-MM-DD format."
                    )
                )
                continue

            if allowed_values:
                value = str(current_value).strip()

                if value not in allowed_values:
                    issues.append(
                        create_issue(
                            issue_type="invalid_allowed_value",
                            row=row,
                            field_name=field_name,
                            current_value=current_value,
                            suggested_value=allowed_values,
                            reason=f"{field_name} must be one of the allowed values."
                        )
                    )

    return df, issues


def load_target_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as file:
        return json.load(file)


if __name__ == "__main__":
    target_schema = {
        "entity": "sales_deal",
        "fields": {
            "country": {
                "type": "string",
                "required": True
            },
            "deal_id": {
                "type": "string",
                "required": True
            },
            "company_name": {
                "type": "string",
                "required": True
            },
            "contact_email": {
                "type": "string",
                "format": "email",
                "required": False
            },
            "deal_value_usd": {
                "type": "number",
                "required": True
            },
            "sales_stage": {
                "type": "string",
                "required": True,
                "allowed_values": [
                    "qualification",
                    "proposal",
                    "negotiation",
                    "closed_won",
                    "closed_lost"
                ]
            },
            "expected_close_date": {
                "type": "string",
                "format": "date",
                "required": True
            },
            "customer_segment": {
                "type": "string",
                "required": False
            },
            "tax_id": {
                "type": "string",
                "required": False
            },
            "source_file": {
                "type": "string",
                "required": True
            }
        }
    }

    data = {
        "country": ["India", "USA", ""],
        "deal_id": ["501", "1001", "DE-801"],
        "company_name": ["Tata Solutions", "Acme Corp", ""],
        "contact_email": [
            "rajesh.k@tata.com",
            "bad-email",
            "test@test.com"
        ],
        "deal_value_usd": [30000.0, "not-number", 102600.0],
        "sales_stage": [
            "proposal",
            "hot_lead",
            "qualification"
        ],
        "expected_close_date": [
            "2026-10-15",
            "09/15/2026",
            "2026-10-15"
        ],
        "customer_segment": ["A1", "Enterprise", "Kat-A"],
        "tax_id": ["27AAAAA0000A1Z5", "", "DE123456789"],
        "source_file": [
            "crm_export_india.csv",
            "crm_export_us.csv",
            "crm_export_germany.xlsx"
        ],
        "source_row_number": [1, 2, 3]
    }

    df = pd.DataFrame(data)

    print("Before:")
    print(df)

    df, issues = validate_json_schema(df, target_schema)

    print("\nAfter:")
    print(df)

    print("\nIssues:")
    for issue in issues:
        print(issue)