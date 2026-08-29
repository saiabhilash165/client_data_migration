CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    action TEXT,
    details TEXT
);

CREATE TABLE IF NOT EXISTS record_hashes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_key TEXT UNIQUE,
    record_hash TEXT,
    last_pushed_at TEXT
);

CREATE TABLE IF NOT EXISTS api_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id TEXT,
    action TEXT,
    status TEXT,
    response TEXT,
    error TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_type TEXT,
    source_file TEXT,
    row_number INTEGER,
    field_name TEXT,
    current_value TEXT,
    suggested_value TEXT,
    reason TEXT,
    status TEXT,
    created_at TEXT,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS sales_deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_key TEXT UNIQUE,
    country TEXT,
    deal_id TEXT,
    company_name TEXT,
    contact_email TEXT,
    deal_value_usd REAL,
    sales_stage TEXT,
    expected_close_date TEXT,
    customer_segment TEXT,
    tax_id TEXT,
    source_file TEXT,
    raw_json TEXT,
    created_at TEXT,
    updated_at TEXT
);