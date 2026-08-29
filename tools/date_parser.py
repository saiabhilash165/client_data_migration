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


DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y.%m.%d",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%d.%m.%Y"
]


def try_parse(value, date_format):
    try:
        parsed = datetime.strptime(str(value).strip(), date_format)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return None


def infer_column_date_format(series):
    format_scores = {}

    values = [
        value for value in series
        if not pd.isna(value) and str(value).strip() != ""
    ]

    for date_format in DATE_FORMATS:
        score = 0

        for value in values:
            parsed = try_parse(value, date_format)

            if parsed:
                score += 1

        format_scores[date_format] = score

    best_format = max(format_scores, key=format_scores.get)
    best_score = format_scores[best_format]

    if best_score == 0:
        return None

    tied_formats = [
        fmt for fmt, score in format_scores.items()
        if score == best_score
    ]

    if len(tied_formats) > 1:
        return None

    return best_format


def parse_date_column(df, column_name="expected_close_date"):
    issues = []

    if column_name not in df.columns:
        return df, issues

    best_format = infer_column_date_format(df[column_name])

    if best_format is None:
        for _, row in df.iterrows():
            current_value = row.get(column_name)

            if pd.isna(current_value) or str(current_value).strip() == "":
                issues.append(
                    create_issue(
                        issue_type="missing_date",
                        row=row,
                        field_name=column_name,
                        current_value=current_value,
                        reason="Expected close date is missing."
                    )
                )
                continue

            issues.append(
                create_issue(
                    issue_type="unknown_date_format",
                    row=row,
                    field_name=column_name,
                    current_value=current_value,
                    reason="Date format could not be inferred from the column."
                )
            )

        return df, issues

    for index, row in df.iterrows():
        current_value = row.get(column_name)

        if pd.isna(current_value) or str(current_value).strip() == "":
            issues.append(
                create_issue(
                    issue_type="missing_date",
                    row=row,
                    field_name=column_name,
                    current_value=current_value,
                    reason="Expected close date is missing."
                )
            )
            continue

        parsed_value = try_parse(current_value, best_format)

        if parsed_value:
            df.at[index, column_name] = parsed_value
        else:
            issues.append(
                create_issue(
                    issue_type="date_parse_failed",
                    row=row,
                    field_name=column_name,
                    current_value=current_value,
                    reason=f"Date could not be parsed using inferred format {best_format}."
                )
            )

    return df, issues


if __name__ == "__main__":
    data = {
        "expected_close_date": [
            "15/10/2026",
            "05/09/2026",
            "30/11/2026",
            "01/02/2026"
        ],
        "source_file": [
            "crm_export_india.csv",
            "crm_export_india.csv",
            "crm_export_india.csv",
            "crm_export_india.csv"
        ],
        "source_row_number": [1, 2, 3, 4]
    }

    df = pd.DataFrame(data)

    print("Before:")
    print(df)

    df, issues = parse_date_column(df)

    print("\nAfter:")
    print(df)

    print("\nIssues:")
    for issue in issues:
        print(issue)