import json
import pandas as pd

from tools.file_reader import read_multiple_files, get_source_columns, get_sample_rows
from tools.trim_spaces import trim_spaces_in_columns
from tools.casing import lowercase_columns
from tools.sales_stage import normalize_sales_stage_column
from tools.date_parser import parse_date_column
from tools.email_validator import validate_email_column
from tools.currency_converter import convert_currency_column
from tools.deduplicate import deduplicate_records
from tools.json_validator import validate_json_schema, load_target_schema
from tools.delta import check_delta
from tools.api_push import push_records_to_api
from tools.audit import add_audit_log

from llm.groq_client import GroqClient
from llm.prompts import COLUMN_MAPPING_SYSTEM_PROMPT, build_column_mapping_prompt


def add_state_log(state, action, details=None):
    if "audit_log" not in state:
        state["audit_log"] = []

    log = add_audit_log(action, details)
    state["audit_log"].append(log)


def create_issue(issue_type, field_name, current_value, reason, source_file=None, row_number=None, suggested_value=None):
    return {
        "issue_type": issue_type,
        "source_file": source_file,
        "row_number": row_number,
        "field_name": field_name,
        "current_value": current_value,
        "suggested_value": suggested_value,
        "reason": reason,
        "status": "open"
    }


def clean_llm_json(response_text):
    text = response_text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()

    elif text.startswith("```"):
        text = text.replace("```", "").strip()

    return json.loads(text)


def load_schema_node(state):
    schema_path = state.get("target_schema_path", "config/target_schema.json")
    state["target_schema"] = load_target_schema(schema_path)
    state["current_status"] = "Target schema loaded"

    add_state_log(state, "target_schema_loaded", {"schema_path": schema_path})

    return state


def read_files_node(state):
    file_paths = state.get("file_paths", [])

    raw_tables = read_multiple_files(file_paths)

    state["raw_tables"] = raw_tables
    state["review_queue"] = state.get("review_queue", [])
    state["current_status"] = "Files read successfully"

    for file_name, df in raw_tables.items():
        add_state_log(
            state,
            "file_read",
            {
                "file_name": file_name,
                "row_count": len(df),
                "columns": list(df.columns)
            }
        )

    return state


def llm_column_mapping_node(state):
    raw_tables = state["raw_tables"]
    target_schema = state["target_schema"]

    groq_client = GroqClient()
    llm_mappings = {}

    for file_name, df in raw_tables.items():
        source_columns = get_source_columns(df)
        sample_rows = get_sample_rows(df, count=3)

        prompt = build_column_mapping_prompt(
            file_name=file_name,
            source_columns=source_columns,
            sample_rows=sample_rows,
            target_schema=target_schema
        )

        prompt += """

Also return source_currency for the revenue/deal value column.
Example:
If source column is Forecasted_Rev_INR, source_currency should be INR.
If source column is Umsatz_Prognose_EUR, source_currency should be EUR.
If source column is Deal_Value_USD, source_currency should be USD.
For non-money columns, source_currency should be null.

Return each mapping item like this:
{
  "source_column": "column name",
  "target_field": "target field or null",
  "confidence": 0.0,
  "source_currency": "USD/EUR/INR or null",
  "reason": "short reason"
}
"""

        response = groq_client.chat(
            user_prompt=prompt,
            system_prompt=COLUMN_MAPPING_SYSTEM_PROMPT,
            temperature=0
        )

        mapping_json = clean_llm_json(response)
        llm_mappings[file_name] = mapping_json

        add_state_log(
            state,
            "llm_column_mapping_done",
            {
                "file_name": file_name,
                "mapping": mapping_json
            }
        )

    state["llm_mappings"] = llm_mappings
    state["current_status"] = "LLM column mapping completed"

    return state


def check_mapping_node(state):
    llm_mappings = state["llm_mappings"]
    review_queue = state.get("review_queue", [])

    approved_mappings = {}
    currency_by_file = {}

    confidence_limit = 0.85

    for file_name, mapping_result in llm_mappings.items():
        approved_mappings[file_name] = {}

        mappings = mapping_result.get("mappings", [])

        for item in mappings:
            source_column = item.get("source_column")
            target_field = item.get("target_field")
            confidence = item.get("confidence", 0)
            reason = item.get("reason")
            source_currency = item.get("source_currency")

            if target_field is None:
                add_state_log(
                    state,
                    "column_ignored",
                    {
                        "file_name": file_name,
                        "source_column": source_column,
                        "reason": reason
                    }
                )
                continue

            if confidence >= confidence_limit:
                approved_mappings[file_name][source_column] = target_field

                add_state_log(
                    state,
                    "column_auto_approved",
                    {
                        "file_name": file_name,
                        "source_column": source_column,
                        "target_field": target_field,
                        "confidence": confidence
                    }
                )

                if target_field == "deal_value_usd":
                    if source_currency:
                        currency_by_file[file_name] = source_currency
                    else:
                        review_queue.append(
                            create_issue(
                                issue_type="unknown_source_currency",
                                source_file=file_name,
                                field_name=target_field,
                                current_value=source_column,
                                reason="Revenue column was mapped, but source currency is unknown."
                            )
                        )

            else:
                review_queue.append(
                    create_issue(
                        issue_type="low_confidence_column_mapping",
                        source_file=file_name,
                        field_name=source_column,
                        current_value=source_column,
                        suggested_value=target_field,
                        reason=f"LLM confidence is low: {confidence}. {reason}"
                    )
                )

    state["approved_mappings"] = approved_mappings
    state["currency_by_file"] = currency_by_file
    state["review_queue"] = review_queue
    state["current_status"] = "Column mapping checked"

    return state


def apply_mapping_node(state):
    raw_tables = state["raw_tables"]
    approved_mappings = state["approved_mappings"]

    mapped_tables = {}

    for file_name, df in raw_tables.items():
        mapping = approved_mappings.get(file_name, {})

        new_df = df.rename(columns=mapping)

        target_fields = list(state["target_schema"]["fields"].keys())
        keep_columns = target_fields + ["source_row_number"]

        available_columns = [
            col for col in keep_columns
            if col in new_df.columns
        ]

        new_df = new_df[available_columns]

        mapped_tables[file_name] = new_df

        add_state_log(
            state,
            "columns_renamed",
            {
                "file_name": file_name,
                "mapping": mapping
            }
        )

    state["mapped_tables"] = mapped_tables
    state["current_status"] = "Source columns renamed to target fields"

    return state


def clean_data_node(state):
    mapped_tables = state["mapped_tables"]
    currency_by_file = state.get("currency_by_file", {})
    review_queue = state.get("review_queue", [])

    cleaned_tables = {}

    for file_name, df in mapped_tables.items():
        text_columns = [
            "country",
            "deal_id",
            "company_name",
            "contact_email",
            "sales_stage",
            "customer_segment",
            "tax_id"
        ]

        df, issues = trim_spaces_in_columns(df, text_columns)
        review_queue.extend(issues)

        string_columns = [
            "country",
            "deal_id",
            "company_name",
            "contact_email",
            "sales_stage",
            "customer_segment",
            "tax_id",
            "source_file"
        ]

        for column in string_columns:
            if column in df.columns:
                df[column] = df[column].apply(
                    lambda value: "" if pd.isna(value) else str(value).strip()
                )

        df, issues = lowercase_columns(df, ["contact_email"])
        review_queue.extend(issues)

        df, issues = normalize_sales_stage_column(df, "sales_stage")
        review_queue.extend(issues)

        df, issues = parse_date_column(df, "expected_close_date")
        review_queue.extend(issues)

        df, issues = validate_email_column(
            df,
            column_name="contact_email",
            required=False
        )
        review_queue.extend(issues)

        source_currency = currency_by_file.get(file_name)

        if source_currency:
            df, issues = convert_currency_column(
                df,
                amount_column="deal_value_usd",
                source_currency=source_currency
            )
            review_queue.extend(issues)
        else:
            if "deal_value_usd" in df.columns:
                review_queue.append(
                    create_issue(
                        issue_type="missing_source_currency",
                        source_file=file_name,
                        field_name="deal_value_usd",
                        current_value="deal_value_usd",
                        reason="Source currency is missing, so currency conversion cannot be done."
                    )
                )

        cleaned_tables[file_name] = df

        add_state_log(
            state,
            "file_cleaned",
            {
                "file_name": file_name,
                "row_count": len(df)
            }
        )

    state["cleaned_tables"] = cleaned_tables
    state["review_queue"] = review_queue
    state["current_status"] = "Data cleaning completed"

    return state


def combine_tables_node(state):
    cleaned_tables = state["cleaned_tables"]

    all_dfs = list(cleaned_tables.values())

    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
    else:
        combined_df = pd.DataFrame()

    state["combined_df"] = combined_df
    state["current_status"] = "All files combined"

    add_state_log(
        state,
        "tables_combined",
        {
            "total_rows": len(combined_df)
        }
    )

    return state


def deduplicate_node(state):
    df = state["combined_df"]
    review_queue = state.get("review_queue", [])

    df, issues = deduplicate_records(
        df,
        key_columns=["country", "deal_id"]
    )

    review_queue.extend(issues)

    state["combined_df"] = df
    state["review_queue"] = review_queue
    state["current_status"] = "Duplicate check completed"

    add_state_log(
        state,
        "deduplication_completed",
        {
            "rows_after_deduplication": len(df),
            "issues_found": len(issues)
        }
    )

    return state


def validate_records_node(state):
    df = state["combined_df"]
    target_schema = state["target_schema"]
    review_queue = state.get("review_queue", [])

    df, issues = validate_json_schema(df, target_schema)

    review_queue.extend(issues)

    state["combined_df"] = df
    state["review_queue"] = review_queue
    state["current_status"] = "JSON validation completed"

    add_state_log(
        state,
        "json_validation_completed",
        {
            "issues_found": len(issues)
        }
    )

    return state


def create_final_json_node(state):
    df = state["combined_df"]
    target_fields = list(state["target_schema"]["fields"].keys())

    final_records = []

    for _, row in df.iterrows():
        record = {}

        for field in target_fields:
            value = row.get(field)

            if pd.isna(value):
                value = None

            record[field] = value

        final_records.append(record)

    state["final_json_records"] = final_records
    state["current_status"] = "Final JSON records created"

    add_state_log(
        state,
        "final_json_created",
        {
            "record_count": len(final_records)
        }
    )

    return state


def delta_check_node(state):
    records = state["final_json_records"]
    df = pd.DataFrame(records)

    previous_hashes = state.get("previous_hashes", {})

    delta_result = check_delta(
        df,
        previous_hashes=previous_hashes,
        key_columns=["country", "deal_id"]
    )

    state["delta_result"] = delta_result
    state["current_status"] = "Delta check completed"

    add_state_log(
        state,
        "delta_check_completed",
        {
            "to_create": len(delta_result["to_create"]),
            "to_update": len(delta_result["to_update"]),
            "to_skip": len(delta_result["to_skip"])
        }
    )

    return state


def push_to_api_node(state):
    api_url = state.get("api_url")

    if not api_url:
        state["api_results"] = []
        state["current_status"] = "API URL missing, push skipped"

        add_state_log(
            state,
            "api_push_skipped",
            {
                "reason": "api_url not provided"
            }
        )

        return state

    delta_result = state["delta_result"]

    results = push_records_to_api(
        to_create=delta_result["to_create"],
        to_update=delta_result["to_update"],
        api_url=api_url
    )

    state["api_results"] = results
    state["current_status"] = "API push completed"

    add_state_log(
        state,
        "api_push_completed",
        {
            "result_count": len(results)
        }
    )

    return state


def stop_for_review_node(state):
    state["current_status"] = "Waiting for human review"

    add_state_log(
        state,
        "waiting_for_human_review",
        {
            "open_issues": len(state.get("review_queue", []))
        }
    )

    return state


def finish_node(state):
    state["current_status"] = "Migration completed"

    add_state_log(
        state,
        "migration_completed",
        {
            "final_records": len(state.get("final_json_records", []))
        }
    )

    return state


def has_open_issues(state):
    review_queue = state.get("review_queue", [])

    for issue in review_queue:
        if issue.get("status") == "open":
            return "needs_review"

    return "continue"