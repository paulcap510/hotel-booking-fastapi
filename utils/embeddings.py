from openai import OpenAI
from config import settings

# This is the sript that OpenAI API uses to create embeddings

client = OpenAI(api_key=settings.openai_api_key)


def get_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding
