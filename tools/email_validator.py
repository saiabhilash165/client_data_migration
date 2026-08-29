import re
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


def is_valid_email(value):
    if not isinstance(value, str):
        return False

    value = value.strip()

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return re.match(email_pattern, value) is not None


def validate_email_column(df, column_name="contact_email", required=False):
    issues = []

    if column_name not in df.columns:
        return df, issues

    for index, row in df.iterrows():
        current_value = row.get(column_name)

        if pd.isna(current_value) or str(current_value).strip() == "":
            if required:
                issues.append(
                    create_issue(
                        issue_type="missing_email",
                        row=row,
                        field_name=column_name,
                        current_value=current_value,
                        reason="Email is required but missing."
                    )
                )
            continue

        cleaned_email = str(current_value).strip().lower()

        if not is_valid_email(cleaned_email):
            issues.append(
                create_issue(
                    issue_type="invalid_email",
                    row=row,
                    field_name=column_name,
                    current_value=current_value,
                    reason="Email format is invalid and cannot be safely fixed."
                )
            )
            continue

        df.at[index, column_name] = cleaned_email

    return df, issues


if __name__ == "__main__":
    data = {
        "contact_email": [
            " rajesh.k@tata.com ",
            "P.SHARMA@RELIANCE.COM",
            "",
            None,
            "john@@company.com",
            "missing-email",
            "valid.user@test.co"
        ],
        "source_file": [
            "crm_export_india.csv",
            "crm_export_india.csv",
            "crm_export_india.csv",
            "crm_export_us.csv",
            "crm_export_us.csv",
            "crm_export_us.csv",
            "crm_export_us.csv"
        ],
        "source_row_number": [1, 2, 3, 4, 5, 6, 7]
    }

    df = pd.DataFrame(data)

    print("Before:")
    print(df)

    df, issues = validate_email_column(
        df,
        column_name="contact_email",
        required=False
    )

    print("\nAfter:")
    print(df)

    print("\nIssues:")
    for issue in issues:
        print(issue)