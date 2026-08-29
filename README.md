# Client Data Migration Agent

An AI-assisted end-to-end client data migration application. It reads CRM exports from multiple regions, maps source columns to a target schema using an LLM, cleans and validates data, escalates uncertain records for human review, generates normalized output, performs delta checks, and pushes records to a mock API backed by SQLite.

---

## Tech Stack

- Python 3.10+
- Pandas
- OpenPyXL
- Streamlit
- FastAPI
- Uvicorn
- Pydantic
- SQLite
- LangGraph
- Groq LLM API
- Requests
- Mermaid for graph visualization

---

## Features

- Upload CSV and Excel CRM files
- LLM-based column mapping
- Data cleaning and normalization
- Currency conversion to USD
- Date normalization
- Sales stage normalization
- Duplicate detection
- Schema validation
- Human review queue in UI
- Safe auto-resolution for selected issues
- Final JSON generation
- Delta detection using record hashes
- API push to mock target system
- SQLite persistence
- Output files saved locally
- LangGraph workflow visualization

---

## Project Structure

```text
client_data_migration/
│
├── app.py
├── visualize_graph.py
├── migration.db
├── README.md
│
├── config/
│   └── target_schema.json
│
├── data/
│   ├── crm_export_india.csv
│   ├── crm_export_us.csv
│   └── crm_export_germany.xlsx
│
├── db/
│   ├── __init__.py
│   ├── database.py
│   └── schema.sql
│
├── graph/
│   ├── __init__.py
│   ├── build_graph.py
│   ├── nodes.py
│   └── state.py
│
├── llm/
│   ├── __init__.py
│   ├── groq_client.py
│   └── prompts.py
│
├── mock_api/
│   ├── __init__.py
│   └── main.py
│
├── tools/
│   ├── __init__.py
│   ├── api_client.py
│   ├── currency_converter.py
│   ├── date_parser.py
│   ├── deduplicator.py
│   ├── file_reader.py
│   ├── json_validator.py
│   ├── record_hasher.py
│   ├── sales_stage_normalizer.py
│   └── text_cleaner.py
│
├── uploaded_files/
│
└── outputs/
    ├── final_migrated_records.json
    ├── cleaned_combined_data.csv
    ├── delta_result.json
    ├── review_queue.json
    ├── audit_log.json
    └── migration_graph.html


Setup

1. Create virtual environment

python -m venv myenv

Activate on Windows:

.\myenv\Scripts\activate

Activate on macOS/Linux:

source myenv/bin/activate


2. Install dependencies

pip install pandas openpyxl streamlit fastapi uvicorn requests pydantic langgraph langchain groq python-dotenv


3. Create .env

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key_here


Run the Application

1. Start mock API

python -m mock_api.main

Mock API runs at:

http://127.0.0.1:8010

Swagger docs:

http://127.0.0.1:8010/docs

Sales deals endpoint:

http://127.0.0.1:8010/sales-deals


2. Start Streamlit app

Open another terminal:

streamlit run app.py

Then open the Streamlit URL shown in terminal.


Usage Flow

Upload CRM source files.
Enter mock API URL:

http://127.0.0.1:8010

Click Run Migration.
Resolve any human review issues.
Click Continue Migration.
Final outputs are generated.
Records are pushed to the mock API and saved in SQLite.


Output Locations

Generated files are saved in:

outputs/

Important output files:

outputs/final_migrated_records.json
outputs/cleaned_combined_data.csv
outputs/delta_result.json
outputs/review_queue.json
outputs/audit_log.json

Records pushed to the target API are stored in:

migration.db

Table:

sales_deals


Database Tables

SQLite database:

migration.db

Tables:

sales_deals
audit_log
review_queue
api_results
record_hashes


Mock API Endpoints

GET /sales-deals
POST /sales-deals
GET /sales-deals/{deal_id}
PUT /sales-deals/{deal_id}
DELETE /sales-deals/{deal_id}
DELETE /sales-deals

The mock API reads and writes to:

migration.db -> sales_deals


Visualize the LangGraph Workflow

Run:

python visualize_graph.py

Generated graph files:

outputs/migration_graph.mmd
outputs/migration_graph.html
outputs/migration_graph.png

Open:

outputs/migration_graph.html


Main Graph Flow

load_schema
   ↓
read_files
   ↓
llm_column_mapping
   ↓
check_mapping
   ├── needs_review → stop_for_review
   └── continue → apply_mapping
                         ↓
                    clean_data
                         ↓
                    combine_tables
                         ↓
                    deduplicate
                         ↓
                    validate_records
                         ├── needs_review → stop_for_review
                         └── continue → create_final_json
                                             ↓
                                        delta_check
                                             ↓
                                        push_to_api
                                             ↓
                                          finish


Common Commands

Run graph directly:

python -m graph.build_graph

Run mock API:

python -m mock_api.main

Run Streamlit UI:

streamlit run app.py

Visualize graph:

python visualize_graph.py


Reset Local State

Stop the app and API, then delete:

migration.db
outputs/
uploaded_files/

Then restart:

python -m mock_api.main
streamlit run app.py


Notes

Run commands from the project root.
Do not run graph/build_graph.py directly. Use:

python -m graph.build_graph

The Streamlit app handles upload, human review, continuation, and output preview.
The mock API persists data in SQLite instead of memory.