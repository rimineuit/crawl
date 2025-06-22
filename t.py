from google import genai

client = genai.Client(api_key="AIzaSyBUwBMbdeD_l6rQ_TJiLuA3eilOrdbm6AQ")

result = client.models.embed_content(
        model="gemini-embedding-exp-03-07",
        contents=["What is the meaning of life?", "rimine was fine"])

print(result.embeddings)