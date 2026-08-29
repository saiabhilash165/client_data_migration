import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv


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


def get_exchange_rates(api_key=None):
    load_dotenv()

    if api_key is None:
        api_key = os.getenv("EXCHANGE_RATE_API_KEY")

    if not api_key:
        raise Exception("EXCHANGE_RATE_API_KEY is missing in .env file.")

    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"

    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get("result") != "success":
        raise Exception("Exchange rate API did not return success.")

    return data["conversion_rates"]


def clean_amount(value):
    if pd.isna(value) or str(value).strip() == "":
        return None

    value = str(value).strip()

    value = re.sub(r"[^0-9,.\-]", "", value)

    if "," in value and "." in value:
        value = value.replace(",", "")

    elif "," in value and "." not in value:
        parts = value.split(",")

        if len(parts[-1]) == 2:
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")

    try:
        return float(value)
    except Exception:
        return None


def convert_amount_to_usd(amount, source_currency, rates):
    source_currency = source_currency.upper()

    if source_currency not in rates:
        raise Exception(f"Currency not found in API rates: {source_currency}")

    if source_currency == "USD":
        return round(amount, 2)

    usd_amount = amount / rates[source_currency]

    return round(usd_amount, 2)


def convert_currency_column(
    df,
    amount_column="deal_value_usd",
    source_currency="USD",
    required=True,
    api_key=None
):
    issues = []

    if amount_column not in df.columns:
        return df, issues

    try:
        rates = get_exchange_rates(api_key)
    except Exception as error:
        for _, row in df.iterrows():
            issues.append(
                create_issue(
                    issue_type="currency_rate_fetch_failed",
                    row=row,
                    field_name=amount_column,
                    current_value=row.get(amount_column),
                    reason=str(error)
                )
            )
        return df, issues

    converted_values = []

    for _, row in df.iterrows():
        current_value = row.get(amount_column)

        amount = clean_amount(current_value)

        if amount is None:
            converted_values.append(current_value)

            if required:
                issues.append(
                    create_issue(
                        issue_type="currency_conversion_failed",
                        row=row,
                        field_name=amount_column,
                        current_value=current_value,
                        reason="Deal value could not be converted to a valid number."
                    )
                )

            continue

        try:
            converted_value = convert_amount_to_usd(
                amount=amount,
                source_currency=source_currency,
                rates=rates
            )

            converted_values.append(converted_value)

        except Exception as error:
            converted_values.append(current_value)

            issues.append(
                create_issue(
                    issue_type="currency_conversion_failed",
                    row=row,
                    field_name=amount_column,
                    current_value=current_value,
                    reason=str(error)
                )
            )

    df[amount_column] = converted_values

    return df, issues


if __name__ == "__main__":
    print("Checking Exchange Rate API...")

    try:
        rates = get_exchange_rates()
        print("API is working.")
        print("Sample rates:")
        print("USD:", rates.get("USD"))
        print("EUR:", rates.get("EUR"))
        print("INR:", rates.get("INR"))
    except Exception as error:
        print("API is not working.")
        print("Reason:", error)

    data = {
        "deal_value_usd": [
            "95,000",
            "240,000",
            "bad-value",
            "",
            "310000.50"
        ],
        "source_file": [
            "crm_export_germany.xlsx",
            "crm_export_germany.xlsx",
            "crm_export_germany.xlsx",
            "crm_export_germany.xlsx",
            "crm_export_germany.xlsx"
        ],
        "source_row_number": [1, 2, 3, 4, 5]
    }

    df = pd.DataFrame(data)

    print("\nBefore:")
    print(df)

    df, issues = convert_currency_column(
        df,
        amount_column="deal_value_usd",
        source_currency="EUR"
    )

    print("\nAfter:")
    print(df)

    print("\nIssues:")
    for issue in issues:
        print(issue)