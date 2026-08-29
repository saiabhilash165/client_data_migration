import os
import pandas as pd


def read_file(file_path):
    file_name = os.path.basename(file_path)

    if file_name.endswith(".csv"):
        df = pd.read_csv(file_path)

    elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        df = pd.read_excel(file_path)

    else:
        raise ValueError(f"Unsupported file type: {file_name}")

    df["source_file"] = file_name
    df["source_row_number"] = range(1, len(df) + 1)

    return df


def read_multiple_files(file_paths):
    raw_tables = {}

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        df = read_file(file_path)
        raw_tables[file_name] = df

    return raw_tables


def get_source_columns(df):
    ignore_columns = ["source_file", "source_row_number"]
    return [col for col in df.columns if col not in ignore_columns]


def get_sample_rows(df, count=3):
    sample_df = df.head(count)
    return sample_df.to_dict(orient="records")


if __name__ == "__main__":
    sample_files = [
        "data/crm_export_india.csv",
        "data/crm_export_us.csv",
        "data/crm_export_germany.xlsx"
    ]

    existing_files = []

    for file_path in sample_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)

    if not existing_files:
        print("No sample files found.")
        print("Please add files inside the data folder.")
    else:
        tables = read_multiple_files(existing_files)

        for file_name, df in tables.items():
            print("\n==============================")
            print(f"File: {file_name}")
            print(f"Rows: {len(df)}")
            print("Columns:")
            print(get_source_columns(df))
            print("Sample rows:")
            print(get_sample_rows(df, count=2))