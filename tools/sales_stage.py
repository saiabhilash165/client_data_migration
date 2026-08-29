import pandas as pd


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


def normalize_stage_value(value):
    if not isinstance(value, str):
        return None

    value = value.strip().lower()

    stage_map = {
        "qualification": "qualification",
        "qualifizierung": "qualification",

        "proposal": "proposal",
        "proposal sent": "proposal",
        "angebot erstellt": "proposal",

        "negotiation": "negotiation",
        "in verhandlung": "negotiation",

        "closed won": "closed_won",
        "closed_won": "closed_won",
        "gewonnen": "closed_won",

        "closed lost": "closed_lost",
        "closed_lost": "closed_lost",
        "verloren": "closed_lost"
    }

    return stage_map.get(value)


def normalize_sales_stage_column(df, column_name="sales_stage"):
    issues = []

    if column_name not in df.columns:
        return df, issues

    for index, row in df.iterrows():
        current_value = row.get(column_name)

        if pd.isna(current_value) or str(current_value).strip() == "":
            issues.append(
                create_issue(
                    issue_type="missing_sales_stage",
                    row=row,
                    field_name=column_name,
                    current_value=current_value,
                    reason="Sales stage is missing."
                )
            )
            continue

        normalized_value = normalize_stage_value(current_value)

        if normalized_value is None:
            issues.append(
                create_issue(
                    issue_type="unknown_sales_stage",
                    row=row,
                    field_name=column_name,
                    current_value=current_value,
                    reason="Sales stage does not match any allowed target value."
                )
            )
            continue

        df.at[index, column_name] = normalized_value

    return df, issues


if __name__ == "__main__":
    data = {
        "sales_stage": [
            "QUALIFICATION",
            "Proposal Sent",
            "IN VERHANDLUNG",
            "Gewonnen",
            " CLOSED LOST ",
            "angebot erstellt",
            "Hot Lead",
            ""
        ],
        "source_file": [
            "crm_export_us.csv",
            "crm_export_us.csv",
            "crm_export_germany.xlsx",
            "crm_export_germany.xlsx",
            "crm_export_india.csv",
            "crm_export_germany.xlsx",
            "crm_export_us.csv",
            "crm_export_india.csv"
        ],
        "source_row_number": [1, 2, 3, 4, 5, 6, 7, 8]
    }

    df = pd.DataFrame(data)

    print("Before:")
    print(df)

    df, issues = normalize_sales_stage_column(df)

    print("\nAfter:")
    print(df)

    print("\nIssues:")
    for issue in issues:
        print(issue)