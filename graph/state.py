from typing import TypedDict, Dict, List, Any


class MigrationState(TypedDict, total=False):
    file_paths: List[str]
    target_schema_path: str
    target_schema: Dict[str, Any]

    raw_tables: Dict[str, Any]
    mapped_tables: Dict[str, Any]
    cleaned_tables: Dict[str, Any]
    combined_df: Any

    llm_mappings: Dict[str, Any]
    approved_mappings: Dict[str, Dict[str, str]]
    currency_by_file: Dict[str, str]

    review_queue: List[Dict[str, Any]]
    final_json_records: List[Dict[str, Any]]

    previous_hashes: Dict[str, str]
    delta_result: Dict[str, Any]

    api_url: str
    api_results: List[Dict[str, Any]]

    audit_log: List[Dict[str, Any]]
    current_status: str