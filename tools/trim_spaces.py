import pandas as pd


def trim_spaces_in_column(df, column_name):
    issues = []

    if column_name not in df.columns:
        return df, issues

    df[column_name] = df[column_name].apply(
        lambda value: value.strip() if isinstance(value, str) else value
    )

    return df, issues


def trim_spaces_in_columns(df, column_names):
    all_issues = []

    for column_name in column_names:
        df, issues = trim_spaces_in_column(df, column_name)
        all_issues.extend(issues)

    return df, all_issues


if __name__ == "__main__":
    data = {
        "company_name": [" Tata Solutions ", "  Wipro Tech", "Mahindra Corp  "],
        "contact_email": [" rajesh.k@tata.com ", "  s.naidu@wipro.com  ", "v.kumar@mahindra.com"]
    }

    df = pd.DataFrame(data)

    print("Before:")
    print(df)

    df, issues = trim_spaces_in_columns(
        df,
        ["company_name", "contact_email"]
    )

    print("\nAfter:")
    print(df)

    print("\nIssues:")
    print(issues)