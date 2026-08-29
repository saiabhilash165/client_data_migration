from datetime import datetime


audit_logs = []


def add_audit_log(action, details=None):
    log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details
    }

    audit_logs.append(log)

    return log


def get_audit_logs():
    return audit_logs


def clear_audit_logs():
    audit_logs.clear()


if __name__ == "__main__":
    add_audit_log(
        action="file_uploaded",
        details={
            "file_name": "crm_export_india.csv",
            "row_count": 10
        }
    )

    add_audit_log(
        action="column_mapped",
        details={
            "source_column": "Forecasted_Rev_INR",
            "target_field": "deal_value_usd",
            "confidence": 0.96
        }
    )

    add_audit_log(
        action="currency_converted",
        details={
            "field": "deal_value_usd",
            "source_currency": "INR",
            "target_currency": "USD"
        }
    )

    print("Audit Logs:")
    for log in get_audit_logs():
        print(log)