import sys
import textwrap

from agents.analyzer import run_analyzer
from agents.perspective import run_perspective_agent
from agents.skeptic import run_skeptic
from utils.combine import build_report
from utils.debate import build_debate_transcript
from dotenv import load_dotenv
load_dotenv(override=True)



def read_user_text():
    print("Paste your idea, plan, or argument below.")
    print("Press ENTER on an empty line to finish.\n")

    lines = []
    for line in sys.stdin:
        if line.strip() == "":
            break
        lines.append(line.rstrip("\n"))
    return "\n".join(lines).strip()


def generate_summary(analyzer_output, perspective_output, skeptic_output):
    """
    Simple handcrafted executive summary for CLI mode.
    """
    return textwrap.dedent(f"""
    This idea has been evaluated by three agents:
    - Analyzer Agent: Structural weaknesses, missing constraints.
    - Perspective Agent: Cross-domain viewpoints you overlooked.
    - Skeptic Agent: Red-team adversarial failure modes.

    Review the report carefully. These blind spots highlight weaknesses
    that could lead to project failure if unaddressed.
    """).strip()


def generate_top_three():
    return textwrap.dedent("""
    1. Pick the most severe assumption or risk and validate it quickly.
    2. Investigate conflicting perspectives highlighted by the Perspective Agent.
    3. Plan countermeasures for at least one worst-case scenario from the Skeptic Agent.
    """).strip()


def generate_recommendations():
    return textwrap.dedent("""
    - Turn each blind spot into a question or experiment.
    - Update your idea and re-run this agent suite to find newly exposed issues.
    - Share this report with a teammate for further review.
    """).strip()


def main():
    print("=" * 60)
    print(" BLIND SPOT FINDER — Multi-Agent CLI")
    print("=" * 60)

    user_text = read_user_text()
    if not user_text:
        print("No input provided.")
        return

    print("\n[1/4] Running Analyzer Agent…")
    analyzer_output = run_analyzer(user_text)

    print("[2/4] Running Perspective Agent…")
    perspective_output = run_perspective_agent(user_text, analyzer_output)

    print("[3/4] Running Skeptic Agent…")
    skeptic_output = run_skeptic(user_text)

    print("[4/4] Building final report…")

    exec_summary = generate_summary(analyzer_output, perspective_output, skeptic_output)
    top_three = generate_top_three()
    recommendations = generate_recommendations()

    report = build_report(
        analyzer_output=analyzer_output,
        perspective_output=perspective_output,
        skeptic_output=skeptic_output,
        exec_summary=exec_summary,
        top_three=top_three,
        recommendations=recommendations,
    )

    print("\n" + report)

    with open("blind_spot_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("\nSaved to blind_spot_report.txt")


if __name__ == "__main__":
    main()
