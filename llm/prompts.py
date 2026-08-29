import json


COLUMN_MAPPING_SYSTEM_PROMPT = """
You are a sales data migration assistant.

Your job is to map source file columns to the target JSON schema fields.

Important rules:
- Use only the source column names, sample values, and target schema.
- Return only valid JSON.
- Do not include markdown.
- Do not include explanations outside JSON.
- If a source column does not match any target field, set target_field to null.
- Give a confidence score between 0 and 1.
"""


def build_column_mapping_prompt(file_name, source_columns, sample_rows, target_schema):
    prompt = f"""
Map the source columns from this sales CRM file to the target JSON schema.

File name:
{file_name}

Source columns:
{json.dumps(source_columns, indent=2)}

Sample rows:
{json.dumps(sample_rows, indent=2)}

Target JSON schema:
{json.dumps(target_schema, indent=2)}

Return JSON only in this exact format:

{{
  "file_name": "{file_name}",
  "mappings": [
    {{
      "source_column": "source column name",
      "target_field": "target field name or null",
      "confidence": 0.0,
      "reason": "short reason"
    }}
  ],
  "unmapped_columns": [
    "source column name"
  ]
}}

Target field must be one of these:
- country
- deal_id
- company_name
- contact_email
- deal_value_usd
- sales_stage
- expected_close_date
- customer_segment
- tax_id
- source_file

Notes:
- source_file is created by the system, so usually no source column maps to source_file.
- Currency columns like EUR, INR, or USD should map to deal_value_usd.
- Extra columns that do not exist in the target schema should map to null.
"""
    return prompt


if __name__ == "__main__":
    sample_file_name = "crm_export_india.csv"

    sample_source_columns = [
        "Country_Name",
        "Deal_Ref_Code",
        "Customer_Account",
        "Email_ID",
        "Forecasted_Rev_INR",
        "Sales_Phase",
        "Target_Date",
        "Account_Grade",
        "GST_Number"
    ]

    sample_rows = [
        {
            "Country_Name": "India",
            "Deal_Ref_Code": "501",
            "Customer_Account": "Tata Solutions",
            "Email_ID": "rajesh.k@tata.com",
            "Forecasted_Rev_INR": "2500000.00",
            "Sales_Phase": "Proposal",
            "Target_Date": "15/10/2026",
            "Account_Grade": "A1",
            "GST_Number": "27AAAAA0000A1Z5"
        }
    ]

    sample_target_schema = {
        "fields": {
            "country": {"type": "string", "required": True},
            "deal_id": {"type": "string", "required": True},
            "company_name": {"type": "string", "required": True},
            "contact_email": {"type": "string", "format": "email", "required": False},
            "deal_value_usd": {"type": "number", "required": True},
            "sales_stage": {"type": "string", "required": True},
            "expected_close_date": {"type": "string", "format": "date", "required": True},
            "customer_segment": {"type": "string", "required": False},
            "tax_id": {"type": "string", "required": False},
            "source_file": {"type": "string", "required": True}
        }
    }

    final_prompt = build_column_mapping_prompt(
        file_name=sample_file_name,
        source_columns=sample_source_columns,
        sample_rows=sample_rows,
        target_schema=sample_target_schema
    )

    print(COLUMN_MAPPING_SYSTEM_PROMPT)
    print(final_prompt)