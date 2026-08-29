Short Write-up: Approach, Escalation Strategy, and Next Steps

Approach

The goal of this project is to build an end-to-end AI-assisted client data migration pipeline. The system takes CRM exports from different source formats such as CSV and Excel, standardizes them into a common target schema, validates the records, allows human review where needed, and finally pushes the cleaned data into a mock target API backed by SQLite.

I designed the migration as a graph-based workflow using LangGraph. Each step in the pipeline is represented as a node, such as schema loading, file reading, LLM-based column mapping, cleaning, deduplication, validation, JSON generation, delta detection, and API push. This makes the flow modular, traceable, and easier to debug.

The application has three main interfaces:

Streamlit UI for uploading files, resolving review issues, and monitoring migration status.
FastAPI mock API that simulates the target system.
SQLite database for persistent storage of migrated sales deals, audit logs, review queue, API results, and record hashes.

The pipeline also saves output files locally, including the final migrated JSON, cleaned combined CSV, review queue, delta result, and audit log.


What the Agent Handles Alone

The agent is allowed to automatically handle deterministic or low-risk transformations. These are cases where the correction is rule-based and unlikely to require business judgment.

Examples:

Trimming whitespace from text fields
Lowercasing email addresses
Converting IDs like deal_id to string
Normalizing known sales stages
Converting currencies when the source currency is known
Parsing dates when the column format is clear
Validating email format
Creating final JSON from validated data
Calculating record hashes for delta detection
Deciding create/update/skip based on hashes
Pushing valid records to the mock API
Saving outputs and audit logs

The agent also auto-resolves safe review issues where the suggested value is clear. For example, if a field is expected to be a string and the value is numeric, the agent can safely convert it to a string.


What Gets Escalated to Human Review

I decided to escalate cases where automation may make the wrong business decision or where the data is ambiguous.

Examples:

Ambiguous date values where the format cannot be confidently inferred
Duplicate records with conflicting values
Missing required fields
Invalid values that do not match allowed schema values
Unknown or missing source currency
Low-confidence column mappings
Invalid records after schema validation

For example, if two records have the same country + deal_id but different deal values, the system should not decide which value is correct without human input. Similarly, if a date like 05/09/2026 appears without enough context, the system should escalate instead of guessing whether it means May 9 or September 5.

The Streamlit UI provides a human-in-the-loop review queue. Users can select an issue, inspect the current value, suggested value, and reason, then apply a resolution. Once all open issues are resolved, the migration can continue.


What I Would Build Next

Next, I would improve the system in these areas:

Better review workflow

Add approval history
Add reviewer name
Add comments
Add bulk approve/reject actions


More robust date inference

Infer date format at file or column level
Use country-based fallback rules
Reduce false escalations


Better LLM mapping confidence

Store mapping confidence scores
Allow users to edit mappings before applying them
Reuse previous mappings for similar files


Production-grade API integration

Add authentication
Add retry logic
Add rate limiting
Add better error handling


Improved observability

Add run IDs
Track each migration run separately
Create a dashboard for success/failure metrics


Database improvements

Add migration run table
Store final records with version history
Support rollback of a migration run


Testing

Add unit tests for cleaning, validation, deduplication, and API push
Add integration tests for full graph execution

Overall, the current system demonstrates a complete AI-assisted migration flow with clear separation between automatic agent actions and human-reviewed decisions.
