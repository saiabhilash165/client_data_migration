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


def normalize_value(value):
    if pd.isna(value):
        return ""

    return str(value).strip().lower()


def rows_are_same(group, compare_columns):
    first_row = group.iloc[0]

    for _, row in group.iterrows():
        for column in compare_columns:
            if normalize_value(row.get(column)) != normalize_value(first_row.get(column)):
                return False

    return True


def get_conflicting_fields(group, compare_columns):
    conflicts = {}

    for column in compare_columns:
        unique_values = set()

        for _, row in group.iterrows():
            unique_values.add(normalize_value(row.get(column)))

        if len(unique_values) > 1:
            conflicts[column] = list(unique_values)

    return conflicts


def deduplicate_records(df, key_columns=None):
    issues = []

    if key_columns is None:
        key_columns = ["country", "deal_id"]

    for key_column in key_columns:
        if key_column not in df.columns:
            return df, issues

    metadata_columns = ["source_file", "source_row_number"]
    compare_columns = [
        col for col in df.columns
        if col not in metadata_columns
    ]

    rows_to_keep = []

    grouped = df.groupby(key_columns, dropna=False)

    for _, group in grouped:
        if len(group) == 1:
            rows_to_keep.append(group.iloc[0])
            continue

        if rows_are_same(group, compare_columns):
            rows_to_keep.append(group.iloc[0])
            continue

        first_row = group.iloc[0]
        conflicts = get_conflicting_fields(group, compare_columns)

        issue = create_issue(
            issue_type="duplicate_conflict",
            row=first_row,
            field_name=", ".join(conflicts.keys()),
            current_value=conflicts,
            suggested_value=None,
            reason="Duplicate records found with conflicting values. Human review is needed."
        )

        issues.append(issue)

        rows_to_keep.append(first_row)

    cleaned_df = pd.DataFrame(rows_to_keep).reset_index(drop=True)

    return cleaned_df, issues


if __name__ == "__main__":
    data = {
        "country": [
            "Germany",
            "Germany",
            "India",
            "India",
            "USA",
            "USA"
        ],
        "deal_id": [
            "DE-802",
            "DE-802",
            "502",
            "502",
            "1003",
            "1003"
        ],
        "company_name": [
            "BMW Group",
            "BMW Group",
            "Reliance Infra",
            "Reliance Infra",
            "Apex Dynamics",
            "Apex Dynamics"
        ],
        "contact_email": [
            "h.weber@bmw.de",
            "h.weber@bmw.de",
            "p.sharma@reliance.com",
            "p.sharma@reliance.com",
            "mark.d@apexdyn.com",
            "mark.d@apexdyn.com"
        ],
        "deal_value_usd": [
            280079.36,
            280079.36,
            78595.15,
            78595.15,
            45000.00,
            47000.00
        ],
        "sales_stage": [
            "negotiation",
            "negotiation",
            "closed_won",
            "closed_won",
            "closed_won",
            "closed_won"
        ],
        "source_file": [
            "crm_export_germany.xlsx",
            "crm_export_germany.xlsx",
            "crm_export_india.csv",
            "crm_export_india.csv",
            "crm_export_us.csv",
            "crm_export_us.csv"
        ],
        "source_row_number": [2, 10, 2, 10, 3, 11]
    }

    df = pd.DataFrame(data)

    print("Before:")
    print(df)

    df, issues = deduplicate_records(df)

    print("\nAfter:")
    print(df)

    print("\nIssues:")
    for issue in issues:
        print(issue)