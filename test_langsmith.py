import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from langsmith import wrappers


gemini_client = genai.Client()

# Wrap for LangSmith tracing
client = wrappers.wrap_gemini(
    gemini_client,
    tracing_extra={
        "tags": ["gemini", "knowbot"],
        "metadata": {
            "integration": "google-genai",
            "project": "KnowBot"
        },
    },
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello in one word.",
)

print("Response:", response.text)
print("Check LangSmith now!")
