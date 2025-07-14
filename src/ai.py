# file: grounded_query.py

import os
from google import genai
from google.genai import types

# 1. Initialize client (for Gemini Developer API)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Prepare the Google Search tool
search_tool = types.Tool(google_search=types.GoogleSearch())

# 3. Issue a grounding query
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What was the latest Indian Premier League match and who won?",
    config=types.GenerateContentConfig(
        tools=[search_tool],
        response_modalities=["TEXT"],
    ),
)

# 4. Output grounded results
print("\n🎯 Answer:\n")
print(response.text)

# 5. Display grounding metadata
cand = response.candidates[0]

print("\n🔍 Search queries used:")
print(cand.grounding_metadata.web_search_queries)

print("\n📚 Sources:")
for chunk in cand.grounding_metadata.grounding_chunks:
    print(f"- {chunk.web.title}: {chunk.web.uri}")

# 6. Save HTML for UI if needed
html = cand.grounding_metadata.search_entry_point.rendered_content
with open("grounded_output.html", "w", encoding="utf-8") as f:
    f.write(html)
print("\n✅ Grounded content HTML saved to grounded_output.html")

# df, news -> gemini (+search) -> tickers (x5) & reason-> opt sortino
