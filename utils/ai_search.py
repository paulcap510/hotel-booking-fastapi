# utils/ai_search.py

from openai import OpenAI
from config import settings
import json

client = OpenAI(api_key=settings.openai_api_key)


def extract_filters(query: str):
    system_prompt = """
You extract structured search filters from a hotel guest's natural language request.
Respond with ONLY a JSON object, no other text, matching this exact shape:

{
  "max_price": number or null,
  "pet_friendly": true, false, or null,
  "has_gym": true, false, or null,
  "has_pool": true, false, or null,
  "has_spa": true, false, or null,
  "free_breakfast": true, false, or null,
  "has_parking": true, false, or null,
  "semantic_query": "a short phrase capturing what the guest cares about in reviews, or null if nothing review-specific was mentioned"
}

Only set a field to true/false if the guest's request clearly implies it. Otherwise use null.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)
