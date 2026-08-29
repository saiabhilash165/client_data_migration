import os
import json
from datetime import datetime

import streamlit as st
import pandas as pd

from graph.build_graph import build_migration_graph

from graph.nodes import (
    validate_records_node,
    create_final_json_node,
    delta_check_node,
    push_to_api_node,
    finish_node
)

from db.database import (
    init_db,
    load_record_hashes,
    save_record_hashes,
    save_review_issues,
    save_api_results,
    save_audit_log
)


UPLOAD_DIR = "uploaded_files"
OUTPUT_DIR = "outputs"


def safe_rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


def save_uploaded_files(uploaded_files):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_paths = []

    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

        with open(file_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        file_paths.append(file_path)

    return file_paths


def save_graph_outputs_to_db(final_state):
    for log in final_state.get("audit_log", []):
        save_audit_log(
            action=log.get("action"),
            details=log.get("details")
        )

    review_queue = final_state.get("review_queue", [])
    if review_queue:
        save_review_issues(review_queue)

    api_results = final_state.get("api_results", [])
    if api_results:
        save_api_results(api_results)

    delta_result = final_state.get("delta_result", {})
    current_hashes = delta_result.get("current_hashes")

    if current_hashes:
        save_record_hashes(current_hashes)


def save_final_outputs_to_files(final_state):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    final_records = final_state.get("final_json_records", [])
    combined_df = final_state.get("combined_df")
    delta_result = final_state.get("delta_result", {})
    api_results = final_state.get("api_results", [])
    review_queue = final_state.get("review_queue", [])
    audit_log = final_state.get("audit_log", [])

    if final_records:
        with open(
            os.path.join(OUTPUT_DIR, "final_migrated_records.json"),
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(final_records, file, indent=2, default=str)

    if combined_df is not None:
        combined_df.to_csv(
            os.path.join(OUTPUT_DIR, "cleaned_combined_data.csv"),
            index=False
        )

    if delta_result:
        delta_summary = {
            "to_create_count": len(delta_result.get("to_create", [])),
            "to_update_count": len(delta_result.get("to_update", [])),
            "to_skip_count": len(delta_result.get("to_skip", [])),
            "to_create": delta_result.get("to_create", []),
            "to_update": delta_result.get("to_update", []),
            "to_skip": delta_result.get("to_skip", [])
        }

        with open(
            os.path.join(OUTPUT_DIR, "delta_result.json"),
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(delta_summary, file, indent=2, default=str)

    if api_results:
        with open(
            os.path.join(OUTPUT_DIR, "api_results.json"),
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(api_results, file, indent=2, default=str)

    if review_queue:
        with open(
            os.path.join(OUTPUT_DIR, "review_queue.json"),
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(review_queue, file, indent=2, default=str)

    if audit_log:
        with open(
            os.path.join(OUTPUT_DIR, "audit_log.json"),
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(audit_log, file, indent=2, default=str)


def add_ui_audit_log(final_state, action, details=None):
    if "audit_log" not in final_state:
        final_state["audit_log"] = []

    final_state["audit_log"].append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details
        }
    )

    return final_state


def get_open_issues(final_state):
    return [
        issue for issue in final_state.get("review_queue", [])
        if issue.get("status") == "open"
    ]


def is_valid_yyyy_mm_dd(value):
    if value is None:
        return False

    try:
        datetime.strptime(str(value).strip(), "%Y-%m-%d")
        return True
    except Exception:
        return False


def get_default_resolution(issue):
    suggested_value = issue.get("suggested_value")

    if isinstance(suggested_value, list) and len(suggested_value) > 0:
        return str(suggested_value[0])

    if suggested_value is not None:
        return str(suggested_value)

    current_value = issue.get("current_value")

    if current_value is None:
        return ""

    return str(current_value)


def convert_resolution_value(field_name, value):
    if field_name == "deal_value_usd":
        try:
            return float(value)
        except Exception:
            return value

    return str(value).strip()


def normalize_combined_df_before_continue(final_state):
    combined_df = final_state.get("combined_df")

    if combined_df is None:
        return final_state

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
        if column in combined_df.columns:
            combined_df[column] = combined_df[column].apply(
                lambda value: "" if pd.isna(value) else str(value).strip()
            )

    if "deal_value_usd" in combined_df.columns:
        combined_df["deal_value_usd"] = pd.to_numeric(
            combined_df["deal_value_usd"],
            errors="coerce"
        )

    final_state["combined_df"] = combined_df

    return final_state


def update_combined_df_value(final_state, issue, resolved_value):
    issue_type = issue.get("issue_type")

    skip_update_issue_types = {
        "duplicate_conflict",
        "low_confidence_column_mapping",
        "unknown_source_currency",
        "missing_source_currency"
    }

    if issue_type in skip_update_issue_types:
        return final_state

    field_name = issue.get("field_name")
    source_file = issue.get("source_file")
    row_number = issue.get("row_number")

    combined_df = final_state.get("combined_df")

    if combined_df is None:
        return final_state

    if not field_name:
        return final_state

    if field_name not in combined_df.columns:
        return final_state

    if "source_file" not in combined_df.columns:
        return final_state

    if "source_row_number" not in combined_df.columns:
        return final_state

    resolved_value = convert_resolution_value(field_name, resolved_value)

    mask = (
        (combined_df["source_file"].astype(str) == str(source_file)) &
        (combined_df["source_row_number"].astype(str) == str(row_number))
    )

    combined_df.loc[mask, field_name] = resolved_value

    final_state["combined_df"] = combined_df

    return final_state


def apply_issue_resolution(final_state, issue_index, resolved_value):
    issue = final_state["review_queue"][issue_index]

    try:
        final_state = update_combined_df_value(
            final_state=final_state,
            issue=issue,
            resolved_value=resolved_value
        )

        issue["status"] = "resolved"
        issue["resolved_value"] = resolved_value
        issue["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        final_state["review_queue"][issue_index] = issue

        final_state = add_ui_audit_log(
            final_state,
            action="human_issue_resolved",
            details={
                "issue_index": issue_index,
                "issue_type": issue.get("issue_type"),
                "source_file": issue.get("source_file"),
                "row_number": issue.get("row_number"),
                "field_name": issue.get("field_name"),
                "resolved_value": resolved_value
            }
        )

    except Exception as error:
        st.error(f"Could not apply resolution: {error}")

    return final_state


def get_value_from_combined_df(final_state, issue):
    combined_df = final_state.get("combined_df")

    if combined_df is None:
        return None

    field_name = issue.get("field_name")
    source_file = issue.get("source_file")
    row_number = issue.get("row_number")

    if not field_name:
        return None

    if field_name not in combined_df.columns:
        return None

    if "source_file" not in combined_df.columns:
        return None

    if "source_row_number" not in combined_df.columns:
        return None

    mask = (
        (combined_df["source_file"].astype(str) == str(source_file)) &
        (combined_df["source_row_number"].astype(str) == str(row_number))
    )

    matched_rows = combined_df.loc[mask]

    if matched_rows.empty:
        return None

    return matched_rows.iloc[0].get(field_name)


def auto_resolve_safe_issues(final_state):
    review_queue = final_state.get("review_queue", [])
    resolved_count = 0

    string_fields = {
        "country",
        "deal_id",
        "company_name",
        "contact_email",
        "sales_stage",
        "customer_segment",
        "tax_id",
        "source_file"
    }

    for issue_index, issue in enumerate(review_queue):
        if issue.get("status") != "open":
            continue

        issue_type = issue.get("issue_type")
        field_name = issue.get("field_name")
        current_value = issue.get("current_value")
        suggested_value = issue.get("suggested_value")

        resolved_value = None
        can_resolve = False

        if issue_type == "ambiguous_date":
            if isinstance(suggested_value, list) and len(suggested_value) > 0:
                resolved_value = suggested_value[0]
                can_resolve = True

        elif issue_type == "invalid_date_format":
            current_df_value = get_value_from_combined_df(final_state, issue)

            if is_valid_yyyy_mm_dd(current_df_value):
                resolved_value = current_df_value
                can_resolve = True

        elif issue_type == "invalid_type" and field_name in string_fields:
            resolved_value = "" if current_value is None else str(current_value).strip()
            can_resolve = True

        elif issue_type == "duplicate_conflict":
            resolved_value = "kept_existing_deduplicated_record"
            can_resolve = True

        elif issue_type == "invalid_allowed_value":
            if isinstance(suggested_value, list) and len(suggested_value) > 0:
                resolved_value = suggested_value[0]
                can_resolve = True

        if can_resolve:
            final_state = apply_issue_resolution(
                final_state=final_state,
                issue_index=issue_index,
                resolved_value=resolved_value
            )
            resolved_count += 1

    final_state = add_ui_audit_log(
        final_state,
        action="safe_issues_auto_resolved",
        details={
            "resolved_count": resolved_count
        }
    )

    return final_state, resolved_count


def continue_migration_after_review(final_state):
    open_issues = get_open_issues(final_state)

    if open_issues:
        final_state["current_status"] = "Waiting for human review"
        return final_state

    final_state = normalize_combined_df_before_continue(final_state)

    final_state = add_ui_audit_log(
        final_state,
        action="continuing_after_human_review",
        details={}
    )

    final_state = validate_records_node(final_state)

    new_open_issues = get_open_issues(final_state)

    if new_open_issues:
        final_state["current_status"] = "Waiting for human review"
        return final_state

    final_state = create_final_json_node(final_state)
    final_state = delta_check_node(final_state)
    final_state = push_to_api_node(final_state)
    final_state = finish_node(final_state)

    save_graph_outputs_to_db(final_state)
    save_final_outputs_to_files(final_state)

    return final_state


st.set_page_config(
    page_title="Client Data Migration",
    layout="wide"
)

st.title("Client Data Migration Agent")

init_db()

if "final_state" not in st.session_state:
    st.session_state["final_state"] = None

uploaded_files = st.file_uploader(
    "Upload source CRM files",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True
)

api_url = st.text_input(
    "Mock API URL",
    value="http://127.0.0.1:8010"
)

col_run, col_clear = st.columns([1, 1])

with col_run:
    run_button = st.button("Run Migration")

with col_clear:
    clear_button = st.button("Clear Current UI State")

if clear_button:
    st.session_state["final_state"] = None
    safe_rerun()

if run_button:
    if not uploaded_files:
        st.error("Please upload at least one file.")
    else:
        with st.spinner("Running migration graph..."):
            file_paths = save_uploaded_files(uploaded_files)

            previous_hashes = load_record_hashes()

            migration_graph = build_migration_graph()

            initial_state = {
                "file_paths": file_paths,
                "target_schema_path": "config/target_schema.json",
                "previous_hashes": previous_hashes,
                "api_url": api_url,
                "review_queue": [],
                "audit_log": []
            }

            final_state = migration_graph.invoke(initial_state)

            save_graph_outputs_to_db(final_state)
            save_final_outputs_to_files(final_state)

            st.session_state["final_state"] = final_state

        st.success("Migration run completed.")
        safe_rerun()


final_state = st.session_state.get("final_state")

if final_state:
    st.subheader("Current Status")
    st.info(final_state.get("current_status"))

    review_queue = final_state.get("review_queue", [])
    open_issues = get_open_issues(final_state)

    st.subheader("Review Queue")

    st.write("Total issues:", len(review_queue))
    st.write("Open issues:", len(open_issues))
    st.write("Resolved issues:", len(review_queue) - len(open_issues))

    if open_issues:
        st.warning(f"{len(open_issues)} issue(s) need human review.")

        col_auto, col_refresh = st.columns([1, 1])

        with col_auto:
            if st.button("Auto-resolve Safe Issues"):
                final_state, resolved_count = auto_resolve_safe_issues(final_state)
                st.session_state["final_state"] = final_state
                st.success(f"Auto-resolved {resolved_count} issue(s).")
                safe_rerun()

        with col_refresh:
            if st.button("Refresh Review Queue"):
                safe_rerun()

        open_issue_options = []

        for issue_index, issue in enumerate(review_queue):
            if issue.get("status") != "open":
                continue

            label = (
                f"#{issue_index} | "
                f"{issue.get('issue_type')} | "
                f"{issue.get('source_file')} | "
                f"Row {issue.get('row_number')} | "
                f"{issue.get('field_name')}"
            )

            open_issue_options.append((label, issue_index))

        selected_label = st.selectbox(
            "Select issue to resolve",
            options=[item[0] for item in open_issue_options],
            key="selected_issue_label"
        )

        selected_issue_index = None

        for label, issue_index in open_issue_options:
            if label == selected_label:
                selected_issue_index = issue_index
                break

        if selected_issue_index is not None:
            selected_issue = review_queue[selected_issue_index]

            st.markdown("### Selected Issue Details")

            st.write("Issue Type:", selected_issue.get("issue_type"))
            st.write("Source File:", selected_issue.get("source_file"))
            st.write("Row Number:", selected_issue.get("row_number"))
            st.write("Field:", selected_issue.get("field_name"))
            st.write("Current Value:", selected_issue.get("current_value"))
            st.write("Suggested Value:", selected_issue.get("suggested_value"))
            st.write("Reason:", selected_issue.get("reason"))

            default_value = get_default_resolution(selected_issue)

            resolved_value = st.text_input(
                "Resolved Value",
                value=default_value,
                key=f"resolved_value_selected_{selected_issue_index}"
            )

            if st.button("Apply Resolution", key="apply_selected_resolution"):
                final_state = apply_issue_resolution(
                    final_state=final_state,
                    issue_index=selected_issue_index,
                    resolved_value=resolved_value
                )

                st.session_state["final_state"] = final_state

                st.success(
                    f"Issue #{selected_issue_index} marked as resolved with value: {resolved_value}"
                )

                safe_rerun()

        with st.expander("Show Full Review Queue"):
            st.dataframe(pd.DataFrame(review_queue), use_container_width=True)

    else:
        st.success("No open review issues.")

        with st.expander("Show Full Review Queue"):
            if review_queue:
                st.dataframe(pd.DataFrame(review_queue), use_container_width=True)
            else:
                st.write("No review issues.")

    st.subheader("Actions")

    final_records = final_state.get("final_json_records", [])

    if open_issues:
        st.info(
            "Resolve all open review issues first. "
            "You can use Auto-resolve Safe Issues or resolve manually."
        )
    else:
        if not final_records:
            if st.button("Continue Migration"):
                with st.spinner("Continuing migration..."):
                    final_state = continue_migration_after_review(final_state)
                    st.session_state["final_state"] = final_state

                if get_open_issues(final_state):
                    st.warning("New validation issues were found. Resolve them and click Continue Migration again.")
                else:
                    st.success("Migration continued successfully.")

                safe_rerun()
        else:
            st.success("Migration completed and final JSON is created.")

    st.subheader("Cleaned Combined Data")

    combined_df = final_state.get("combined_df")

    if combined_df is not None:
        st.dataframe(combined_df, use_container_width=True)
    else:
        st.write("No combined data available.")

    st.subheader("Output Status")

    if os.path.exists(OUTPUT_DIR) and os.listdir(OUTPUT_DIR):
        st.success("Output files generated successfully.")
    else:
        st.info("Output files will be generated after migration is completed.")

    st.subheader("Final JSON Records")

    final_records = final_state.get("final_json_records", [])

    if final_records:
        st.success(f"Final JSON created with {len(final_records)} records.")

        preview_df = pd.DataFrame(final_records)

        st.write("Preview of first 10 records:")
        st.dataframe(preview_df.head(10), use_container_width=True)

        json_text = json.dumps(final_records, indent=2, default=str)

        st.download_button(
            label="Download Final JSON",
            data=json_text,
            file_name="final_migrated_records.json",
            mime="application/json"
        )

        st.info(
            "Full JSON is not displayed in the UI. "
            "Use the download button or check outputs/final_migrated_records.json."
        )
    else:
        st.write("Final JSON not created yet. Resolve review issues first, then click Continue Migration.")

    st.subheader("Delta Result")

    delta_result = final_state.get("delta_result")

    if delta_result:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("To Create", len(delta_result.get("to_create", [])))

        with col2:
            st.metric("To Update", len(delta_result.get("to_update", [])))

        with col3:
            st.metric("To Skip", len(delta_result.get("to_skip", [])))

        with st.expander("Show Delta Details"):
            delta_summary = {
                "to_create_count": len(delta_result.get("to_create", [])),
                "to_update_count": len(delta_result.get("to_update", [])),
                "to_skip_count": len(delta_result.get("to_skip", []))
            }
            st.json(delta_summary)
    else:
        st.write("Delta check not completed yet.")

    st.subheader("API Push Results")

    api_results = final_state.get("api_results", [])

    if api_results:
        st.dataframe(pd.DataFrame(api_results), use_container_width=True)
    else:
        st.write("No API push results.")

    st.subheader("Audit Log")

    audit_log = final_state.get("audit_log", [])

    if audit_log:
        with st.expander("Show Audit Log"):
            st.dataframe(pd.DataFrame(audit_log), use_container_width=True)
    else:
        st.write("No audit logs.")

else:
    st.info("Upload files and click Run Migration to start.")