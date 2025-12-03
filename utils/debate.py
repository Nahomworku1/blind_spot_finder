import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)

DEBATE_PROMPT = """
Create a debate between:
Analyzer • Perspective • Skeptic

Show 2 rounds:
Analyzer:
Perspective:
Skeptic:

Focus on disagreements and contradictions.
"""

def build_debate_transcript(text, analyzer, perspective, skeptic, model_name="gpt-4o-mini", temperature=0.5):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    content = f"""
USER_TEXT:
{text}

ANALYZER_OUTPUT:
{analyzer}

PERSPECTIVE_OUTPUT:
{perspective}

SKEPTIC_OUTPUT:
{skeptic}
"""

    resp = client.chat.completions.create(
        model=model_name,
        temperature=temperature,
        messages=[
            {"role": "system", "content": DEBATE_PROMPT},
            {"role": "user", "content": content}
        ]
    )
    return resp.choices[0].message.content.strip()
