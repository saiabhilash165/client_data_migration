import pandas as pd


def lowercase_column(df, column_name):
    issues = []

    if column_name not in df.columns:
        return df, issues

    df[column_name] = df[column_name].apply(
        lambda value: value.lower() if isinstance(value, str) else value
    )

    return df, issues


def titlecase_column(df, column_name):
    issues = []

    if column_name not in df.columns:
        return df, issues

    df[column_name] = df[column_name].apply(
        lambda value: value.title() if isinstance(value, str) else value
    )

    return df, issues


def lowercase_columns(df, column_names):
    all_issues = []

    for column_name in column_names:
        df, issues = lowercase_column(df, column_name)
        all_issues.extend(issues)

    return df, all_issues


def titlecase_columns(df, column_names):
    all_issues = []

    for column_name in column_names:
        df, issues = titlecase_column(df, column_name)
        all_issues.extend(issues)

    return df, all_issues


if __name__ == "__main__":
    data = {
        "sales_stage": ["QUALIFICATION", "Closed Won", " proposal "],
        "country": ["INDIA", "germany", "usa"]
    }

    df = pd.DataFrame(data)

    print("Before:")
    print(df)

    df, issues = lowercase_columns(df, ["sales_stage", "country"])

    print("\nAfter lowercase:")
    print(df)

    print("\nIssues:")
    print(issues)

    df, issues = titlecase_columns(df, ["country"])

    print("\nAfter titlecase country:")
    print(df)

    print("\nIssues:")
    print(issues)