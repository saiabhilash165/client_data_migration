from langgraph.graph import StateGraph, END

from graph.state import MigrationState
from graph.nodes import (
    load_schema_node,
    read_files_node,
    llm_column_mapping_node,
    check_mapping_node,
    apply_mapping_node,
    clean_data_node,
    combine_tables_node,
    deduplicate_node,
    validate_records_node,
    create_final_json_node,
    delta_check_node,
    push_to_api_node,
    stop_for_review_node,
    finish_node,
    has_open_issues
)


def build_migration_graph():
    graph = StateGraph(MigrationState)

    graph.add_node("load_schema", load_schema_node)
    graph.add_node("read_files", read_files_node)
    graph.add_node("llm_column_mapping", llm_column_mapping_node)
    graph.add_node("check_mapping", check_mapping_node)
    graph.add_node("apply_mapping", apply_mapping_node)
    graph.add_node("clean_data", clean_data_node)
    graph.add_node("combine_tables", combine_tables_node)
    graph.add_node("deduplicate", deduplicate_node)
    graph.add_node("validate_records", validate_records_node)
    graph.add_node("create_final_json", create_final_json_node)
    graph.add_node("delta_check", delta_check_node)
    graph.add_node("push_to_api", push_to_api_node)
    graph.add_node("stop_for_review", stop_for_review_node)
    graph.add_node("finish", finish_node)

    graph.set_entry_point("load_schema")

    graph.add_edge("load_schema", "read_files")
    graph.add_edge("read_files", "llm_column_mapping")
    graph.add_edge("llm_column_mapping", "check_mapping")

    graph.add_conditional_edges(
        "check_mapping",
        has_open_issues,
        {
            "needs_review": "stop_for_review",
            "continue": "apply_mapping"
        }
    )

    graph.add_edge("apply_mapping", "clean_data")
    graph.add_edge("clean_data", "combine_tables")
    graph.add_edge("combine_tables", "deduplicate")
    graph.add_edge("deduplicate", "validate_records")

    graph.add_conditional_edges(
        "validate_records",
        has_open_issues,
        {
            "needs_review": "stop_for_review",
            "continue": "create_final_json"
        }
    )

    graph.add_edge("create_final_json", "delta_check")
    graph.add_edge("delta_check", "push_to_api")
    graph.add_edge("push_to_api", "finish")

    graph.add_edge("stop_for_review", END)
    graph.add_edge("finish", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_migration_graph()

    initial_state = {
        "file_paths": [
            "data/crm_export_india.csv",
            "data/crm_export_us.csv",
            "data/crm_export_germany.xlsx"
        ],
        "target_schema_path": "config/target_schema.json",
        "previous_hashes": {},
        "api_url": ""
    }

    final_state = app.invoke(initial_state)

    print("Current status:")
    print(final_state.get("current_status"))

    print("\nReview queue:")
    for issue in final_state.get("review_queue", []):
        print(issue)

    print("\nFinal JSON records:")
    for record in final_state.get("final_json_records", [])[:3]:
        print(record)

    print("\nAudit log:")
    for log in final_state.get("audit_log", []):
        print(log)