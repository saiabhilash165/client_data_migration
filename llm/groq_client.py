import os
from groq import Groq
from dotenv import load_dotenv


class GroqClient:
    def __init__(self, model="openai/gpt-oss-20b"):
        load_dotenv()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = model

    def chat(self, user_prompt, system_prompt=None, temperature=0, stream=False):
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": user_prompt
        })

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=2048,
            top_p=1,
            reasoning_effort="medium",
            stream=stream,
            stop=None
        )

        if stream:
            response_text = ""
            for chunk in completion:
                content = chunk.choices[0].delta.content or ""
                print(content, end="")
                response_text += content
            print()
            return response_text

        return completion.choices[0].message.content


if __name__ == "__main__":
    groq_client = GroqClient()

    system_prompt = """
You are a helpful assistant for sales data migration.
Return only valid JSON.
"""

    user_prompt = """
Map these source columns to the target schema fields.

Source columns:
[
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

Target fields:
[
  "country",
  "deal_id",
  "company_name",
  "contact_email",
  "deal_value_usd",
  "sales_stage",
  "expected_close_date",
  "customer_segment",
  "tax_id",
  "source_file"
]

Return JSON in this format:
{
  "mappings": [
    {
      "source_column": "source column name",
      "target_field": "target field name or null",
      "confidence": 0.0,
      "reason": "short reason"
    }
  ]
}
"""

    response = groq_client.chat(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0,
        stream=False
    )

    print(response)