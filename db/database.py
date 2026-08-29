import sqlite3
import json
from datetime import datetime


DB_PATH = "migration.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db(schema_path="db/schema.sql"):
    conn = get_connection()

    with open(schema_path, "r", encoding="utf-8") as file:
        schema_sql = file.read()

    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


def save_audit_log(action, details=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO audit_log (timestamp, action, details)
        VALUES (?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            action,
            json.dumps(details, default=str)
        )
    )

    conn.commit()
    conn.close()


def get_audit_logs():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, timestamp, action, details
        FROM audit_log
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


def save_review_issue(issue):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO review_queue (
            issue_type,
            source_file,
            row_number,
            field_name,
            current_value,
            suggested_value,
            reason,
            status,
            created_at,
            resolved_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            issue.get("issue_type"),
            issue.get("source_file"),
            issue.get("row_number"),
            issue.get("field_name"),
            json.dumps(issue.get("current_value"), default=str),
            json.dumps(issue.get("suggested_value"), default=str),
            issue.get("reason"),
            issue.get("status", "open"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            None
        )
    )

    conn.commit()
    conn.close()


def save_review_issues(issues):
    for issue in issues:
        save_review_issue(issue)


def get_open_review_issues():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            issue_type,
            source_file,
            row_number,
            field_name,
            current_value,
            suggested_value,
            reason,
            status
        FROM review_queue
        WHERE status = 'open'
        ORDER BY id
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


def save_record_hashes(record_hashes):
    conn = get_connection()
    cursor = conn.cursor()

    for record_key, record_hash in record_hashes.items():
        cursor.execute(
            """
            INSERT INTO record_hashes (record_key, record_hash, last_pushed_at)
            VALUES (?, ?, ?)
            ON CONFLICT(record_key)
            DO UPDATE SET
                record_hash = excluded.record_hash,
                last_pushed_at = excluded.last_pushed_at
            """,
            (
                record_key,
                record_hash,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

    conn.commit()
    conn.close()


def load_record_hashes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT record_key, record_hash
        FROM record_hashes
        """
    )

    rows = cursor.fetchall()
    conn.close()

    hashes = {}

    for record_key, record_hash in rows:
        hashes[record_key] = record_hash

    return hashes


def save_api_result(result):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO api_results (
            deal_id,
            action,
            status,
            response,
            error,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            result.get("deal_id"),
            result.get("action"),
            result.get("status"),
            json.dumps(result.get("response"), default=str),
            result.get("error"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()


def save_api_results(results):
    for result in results:
        save_api_result(result)

def create_record_key(country, deal_id):
    return f"{str(country).strip()}_{str(deal_id).strip()}"


def normalize_sales_deal_record(record):
    return {
        "country": "" if record.get("country") is None else str(record.get("country")).strip(),
        "deal_id": "" if record.get("deal_id") is None else str(record.get("deal_id")).strip(),
        "company_name": "" if record.get("company_name") is None else str(record.get("company_name")).strip(),
        "contact_email": "" if record.get("contact_email") is None else str(record.get("contact_email")).strip(),
        "deal_value_usd": record.get("deal_value_usd"),
        "sales_stage": "" if record.get("sales_stage") is None else str(record.get("sales_stage")).strip(),
        "expected_close_date": "" if record.get("expected_close_date") is None else str(record.get("expected_close_date")).strip(),
        "customer_segment": "" if record.get("customer_segment") is None else str(record.get("customer_segment")).strip(),
        "tax_id": "" if record.get("tax_id") is None else str(record.get("tax_id")).strip(),
        "source_file": "" if record.get("source_file") is None else str(record.get("source_file")).strip()
    }


def create_sales_deal(record):
    conn = get_connection()
    cursor = conn.cursor()

    normalized = normalize_sales_deal_record(record)
    record_key = create_record_key(
        normalized["country"],
        normalized["deal_id"]
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute(
            """
            INSERT INTO sales_deals (
                record_key,
                country,
                deal_id,
                company_name,
                contact_email,
                deal_value_usd,
                sales_stage,
                expected_close_date,
                customer_segment,
                tax_id,
                source_file,
                raw_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_key,
                normalized["country"],
                normalized["deal_id"],
                normalized["company_name"],
                normalized["contact_email"],
                normalized["deal_value_usd"],
                normalized["sales_stage"],
                normalized["expected_close_date"],
                normalized["customer_segment"],
                normalized["tax_id"],
                normalized["source_file"],
                json.dumps(normalized, default=str),
                now,
                now
            )
        )

        conn.commit()

        result = {
            "created": True,
            "record_key": record_key,
            "record": normalized
        }

    except sqlite3.IntegrityError:
        result = {
            "created": False,
            "record_key": record_key,
            "record": normalized
        }

    conn.close()

    return result


def update_sales_deal(record):
    conn = get_connection()
    cursor = conn.cursor()

    normalized = normalize_sales_deal_record(record)
    record_key = create_record_key(
        normalized["country"],
        normalized["deal_id"]
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        UPDATE sales_deals
        SET
            country = ?,
            deal_id = ?,
            company_name = ?,
            contact_email = ?,
            deal_value_usd = ?,
            sales_stage = ?,
            expected_close_date = ?,
            customer_segment = ?,
            tax_id = ?,
            source_file = ?,
            raw_json = ?,
            updated_at = ?
        WHERE record_key = ?
        """,
        (
            normalized["country"],
            normalized["deal_id"],
            normalized["company_name"],
            normalized["contact_email"],
            normalized["deal_value_usd"],
            normalized["sales_stage"],
            normalized["expected_close_date"],
            normalized["customer_segment"],
            normalized["tax_id"],
            normalized["source_file"],
            json.dumps(normalized, default=str),
            now,
            record_key
        )
    )

    updated_count = cursor.rowcount

    conn.commit()
    conn.close()

    return {
        "updated": updated_count > 0,
        "record_key": record_key,
        "record": normalized
    }


def upsert_sales_deal(record):
    existing = get_sales_deal_by_key(
        country=record.get("country"),
        deal_id=record.get("deal_id")
    )

    if existing:
        return update_sales_deal(record)

    return create_sales_deal(record)


def get_sales_deal_by_key(country, deal_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    record_key = create_record_key(country, deal_id)

    cursor.execute(
        """
        SELECT *
        FROM sales_deals
        WHERE record_key = ?
        """,
        (record_key,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def get_all_sales_deals():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sales_deals
        ORDER BY id
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_sales_deals_by_deal_id(deal_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sales_deals
        WHERE deal_id = ?
        ORDER BY id
        """,
        (str(deal_id),)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def delete_sales_deals_by_deal_id(deal_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM sales_deals
        WHERE deal_id = ?
        """,
        (str(deal_id),)
    )

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted_count


def clear_sales_deals():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sales_deals")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()

    save_audit_log(
        action="database_initialized",
        details={"db_path": DB_PATH}
    )

    print("Database initialized successfully.")

    print("\nAudit logs:")
    for row in get_audit_logs():
        print(row)