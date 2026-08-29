import requests


def push_create_records(records, api_url):
    results = []

    for record in records:
        try:
            response = requests.post(
                f"{api_url}/sales-deals",
                json=record,
                timeout=10
            )

            if response.status_code in [200, 201]:
                results.append({
                    "action": "create",
                    "deal_id": record.get("deal_id"),
                    "status": "success",
                    "response": response.json()
                })
            else:
                results.append({
                    "action": "create",
                    "deal_id": record.get("deal_id"),
                    "status": "failed",
                    "error": response.text
                })

        except Exception as error:
            results.append({
                "action": "create",
                "deal_id": record.get("deal_id"),
                "status": "failed",
                "error": str(error)
            })

    return results


def push_update_records(records, api_url):
    results = []

    for record in records:
        deal_id = record.get("deal_id")

        try:
            response = requests.put(
                f"{api_url}/sales-deals/{deal_id}",
                json=record,
                timeout=10
            )

            if response.status_code in [200, 201]:
                results.append({
                    "action": "update",
                    "deal_id": deal_id,
                    "status": "success",
                    "response": response.json()
                })
            else:
                results.append({
                    "action": "update",
                    "deal_id": deal_id,
                    "status": "failed",
                    "error": response.text
                })

        except Exception as error:
            results.append({
                "action": "update",
                "deal_id": deal_id,
                "status": "failed",
                "error": str(error)
            })

    return results


def push_records_to_api(to_create, to_update, api_url):
    results = []

    create_results = push_create_records(to_create, api_url)
    update_results = push_update_records(to_update, api_url)

    results.extend(create_results)
    results.extend(update_results)

    return results


if __name__ == "__main__":
    api_url = "http://127.0.0.1:8000"

    sample_create_records = [
        {
            "country": "India",
            "deal_id": "501",
            "company_name": "Tata Solutions",
            "contact_email": "rajesh.k@tata.com",
            "deal_value_usd": 30000.0,
            "sales_stage": "proposal",
            "expected_close_date": "2026-10-15",
            "customer_segment": "A1",
            "tax_id": "27AAAAA0000A1Z5",
            "source_file": "crm_export_india.csv"
        }
    ]

    sample_update_records = [
        {
            "country": "USA",
            "deal_id": "1001",
            "company_name": "Acme Corp",
            "contact_email": "john.smith@acme.com",
            "deal_value_usd": 125000.0,
            "sales_stage": "qualification",
            "expected_close_date": "2026-09-15",
            "customer_segment": "Enterprise",
            "tax_id": "",
            "source_file": "crm_export_us.csv"
        }
    ]

    print("Pushing records to API...")

    results = push_records_to_api(
        to_create=sample_create_records,
        to_update=sample_update_records,
        api_url=api_url
    )

    print("\nResults:")
    for result in results:
        print(result)