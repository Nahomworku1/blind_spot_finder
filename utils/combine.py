from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True)

def _load():
    path = Path(__file__).resolve().parents[1] / "prompts" / "report_template.txt"
    return path.read_text()

def build_report(analyzer_output, perspective_output, skeptic_output, exec_summary, top_three, recommendations):
    template = _load()
    return (
        template.replace("{ANALYZER_OUTPUT}", analyzer_output)
                .replace("{PERSPECTIVE_OUTPUT}", perspective_output)
                .replace("{SKEPTIC_OUTPUT}", skeptic_output)
                .replace("{EXEC_SUMMARY}", exec_summary)
                .replace("{TOP_THREE}", top_three)
                .replace("{RECOMMENDATIONS}", recommendations)
    )

def build_severity_bars():
    return {
        "Assumptions": 70,
        "Risks": 80,
        "Perspectives": 65,
        "Evidence": 60,
        "Fragility": 75,
    }
