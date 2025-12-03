import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)


def _load_prompt():
    path = Path(__file__).resolve().parents[1] / "prompts" / "skeptic_prompt.txt"
    return path.read_text(encoding="utf-8")


def run_skeptic(text, model_name="gpt-4o-mini", temperature=0.5):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = _load_prompt()

    resp = client.chat.completions.create(
        model=model_name,
        temperature=temperature,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"USER_TEXT:\n{text}"}
        ]
    )
    return resp.choices[0].message.content.strip()
