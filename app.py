import os
from textwrap import dedent

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

from agents.analyzer import run_analyzer
from agents.perspective import run_perspective_agent
from agents.skeptic import run_skeptic
from utils.combine import build_report, build_severity_bars
from utils.debate import build_debate_transcript
from dotenv import load_dotenv
load_dotenv(override=True)
# Load environment (.env overrides Windows/user variables)


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ------------------------------
# FULL MULTI-AGENT ANALYSIS
# ------------------------------
def run_full_analysis(idea_a: str, model_name: str, temperature: float):
    """
    Main pipeline used by the big 'Run Multi-Agent Analysis' button.
    Returns:
    - Overview report (Markdown)
    - Analyzer output (Markdown)
    - Perspective output (Markdown)
    - Skeptic output (Markdown)
    - Severity bars (HTML)
    - Status message (Markdown)
    """
    if not idea_a or not idea_a.strip():
        return (
            "⚠️ Please enter an idea, plan, or argument first.",
            "",
            "",
            "",
            "",
            "No input provided.",
        )

    try:
        # Run agents
        analyzer_out = run_analyzer(
            idea_a, model_name=model_name, temperature=temperature
        )
        perspective_out = run_perspective_agent(
            idea_a,
            analyzer_out,
            model_name=model_name,
            temperature=min(1.0, temperature + 0.1),
        )
        skeptic_out = run_skeptic(
            idea_a, model_name=model_name, temperature=min(1.0, temperature + 0.1)
        )

        # Handcrafted high-level summary
        exec_summary = dedent(
            """
            This idea has been evaluated by three specialized agents:

            - **Analyzer Agent** — extracts structural weaknesses, hidden assumptions, and missing constraints.  
            - **Perspective Agent** — applies alternate expert viewpoints to reveal what you didn't consider.  
            - **Skeptic Agent** — aggressively red-teams the idea, surfacing failure modes and fragility.

            Use this report as a **pre-mortem**: fix these issues *before* you invest time, money, or reputation.
            """
        ).strip()

        top_three = dedent(
            """
            1. Identify the single most dangerous assumption and validate it immediately.  
            2. Resolve any conflicts between perspectives (e.g., user, technical, ethical).  
            3. Prepare mitigation for at least one worst-case scenario raised by the Skeptic Agent.
            """
        ).strip()

        recommendations = dedent(
            """
            - Turn each blind spot into a concrete experiment or validation step.  
            - Re-run this multi-agent analysis after you update the idea.  
            - Share this report with a colleague and ask where they disagree with it.
            """
        ).strip()

        report = build_report(
            analyzer_output=analyzer_out,
            perspective_output=perspective_out,
            skeptic_output=skeptic_out,
            exec_summary=exec_summary,
            top_three=top_three,
            recommendations=recommendations,
        )

        severity_html = render_severity_bars()

        status = "✅ Multi-agent analysis complete."

        return (
            report,
            analyzer_out,
            perspective_out,
            skeptic_out,
            severity_html,
            status,
        )

    except Exception as e:
        # If something blows up (API, network, etc.), show a friendly error
        err_msg = f"❌ Error during analysis: `{type(e).__name__}` — {e}"
        return (err_msg, "", "", "", "", err_msg)


# ------------------------------
# HEATMAP / SEVERITY BARS
# ------------------------------
def render_severity_bars() -> str:
    """
    Build a simple horizontal bar 'heatmap' from the dict
    returned by utils.combine.build_severity_bars().
    """
    data = build_severity_bars()
    if not isinstance(data, dict):
        return "<p>⚠️ Could not compute severity distribution.</p>"

    html = "<div style='display:flex;flex-direction:column;gap:12px;'>"
    for label, score in data.items():
        safe_label = str(label)
        try:
            score = float(score)
        except Exception:
            score = 0.0
        score = max(0.0, min(100.0, score))
        html += f"""
        <div style="font-family: system-ui, sans-serif; font-size: 0.9rem;">
            <div style="display:flex;justify-content:space-between;">
                <strong>{safe_label}</strong>
                <span>{score:.0f}%</span>
            </div>
            <div style="
                background: #222;
                height: 10px;
                border-radius: 999px;
                overflow: hidden;
                box-shadow: inset 0 0 4px rgba(0,0,0,0.7);
            ">
                <div style="
                    height: 10px;
                    width: {score:.0f}%;
                    background: linear-gradient(90deg, #ff4d4d, #ffb347);
                "></div>
            </div>
        </div>
        """
    html += "</div>"
    return html


# ------------------------------
# IDEA COMPARISON
# ------------------------------
def compare_ideas(
    idea_a: str, idea_b: str, model_name: str, temperature: float
) -> str:
    if not idea_a or not idea_a.strip() or not idea_b or not idea_b.strip():
        return "⚠️ Please provide **both** Idea A and Idea B for comparison."

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "❌ OPENAI_API_KEY missing. Check your .env file."

    client = OpenAI(api_key=api_key)

    system_prompt = dedent(
        """
        You are a rigorous evaluator comparing two ideas.

        Compare IDEA A vs IDEA B on:
        - Strengths
        - Weaknesses
        - Blind spots
        - Risk profile
        - Robustness under stress
        - Likely success conditions

        Then give:
        - A short verdict on which is more robust
        - One suggestion to improve IDEA A
        - One suggestion to improve IDEA B

        Be concise but concrete.
        """
    ).strip()

    user_content = f"IDEA A:\n{idea_a}\n\nIDEA B:\n{idea_b}"

    resp = client.chat.completions.create(
        model=model_name,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    return resp.choices[0].message.content.strip()


# ------------------------------
# DEBATE VIEW
# ------------------------------
def debate_view(idea_a: str, model_name: str, temperature: float) -> str:
    """
    Generate a friendly but adversarial debate transcript
    between Analyzer, Perspective, and Skeptic.
    """
    if not idea_a or not idea_a.strip():
        return "⚠️ Please enter an idea first."

    analyzer_out = run_analyzer(idea_a, model_name=model_name, temperature=temperature)
    perspective_out = run_perspective_agent(
        idea_a, analyzer_out, model_name=model_name, temperature=temperature
    )
    skeptic_out = run_skeptic(
        idea_a, model_name=model_name, temperature=min(1.0, temperature + 0.1)
    )

    transcript = build_debate_transcript(
        idea_a, analyzer_out, perspective_out, skeptic_out, model_name=model_name
    )

    return transcript


# ------------------------------
# BUILD GRADIO INTERFACE
# ------------------------------
def create_ui():
    with gr.Blocks() as demo:
        # HEADER
        gr.Markdown(
            """
            # 🧠 Blind Spot Finder — Multi-Agent Critical Reasoner  
            **Analyzer • Perspective • Skeptic Agents**

            Paste an idea, plan, argument, or product concept.  
            This system will **attack it from multiple angles** and surface hidden risks, assumptions, and missing perspectives.
            """,
        )

        with gr.Row():
            # LEFT COLUMN: INPUT & SETTINGS
            with gr.Column(scale=2):
                idea_a = gr.Textbox(
                    label="Primary Idea / Plan (Idea A)",
                    placeholder="Example: I want to build an app that recommends playlists based on a user's mood...",
                    lines=10,
                )

                idea_b = gr.Textbox(
                    label="Idea B (Optional, for comparison)",
                    placeholder="Optional: second idea to compare against Idea A.",
                    lines=6,
                )

                model_name = gr.Dropdown(
                    choices=["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
                    value=DEFAULT_MODEL,
                    label="Model",
                )

                temperature = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.4,
                    step=0.05,
                    label="Creativity (temperature)",
                )

                with gr.Row():
                    run_btn = gr.Button(
                        "🔍 Run Multi-Agent Analysis", variant="primary", scale=3
                    )
                    compare_btn = gr.Button("⚖️ Compare Idea A vs Idea B", scale=2)

                status_md = gr.Markdown("Ready.", elem_id="status-text")

            # RIGHT COLUMN: OUTPUT TABS
            with gr.Column(scale=3):
                with gr.Tab("📋 Overview Report"):
                    overview_report = gr.Markdown(
                        value="The full blind-spot report will appear here."
                    )
                    gr.Markdown("### Blind Spot Severity Snapshot")
                    severity_html = gr.HTML()

                with gr.Tab("🧬 Agent Outputs"):
                    gr.Markdown("### Analyzer Agent")
                    analyzer_md = gr.Markdown()

                    gr.Markdown("### Perspective Agent")
                    perspective_md = gr.Markdown()

                    gr.Markdown("### Skeptic Agent")
                    skeptic_md = gr.Markdown()

                with gr.Tab("⚔️ Debate View"):
                    gr.Markdown(
                        "Simulated debate between Analyzer, Perspective, and Skeptic."
                    )
                    debate_md = gr.Markdown()

                with gr.Tab("⚖️ Idea Comparison (A vs B)"):
                    comparison_md = gr.Markdown(
                        "Provide both Idea A and Idea B, then click **Compare**."
                    )

        # ------------------------------
        # WIRING BUTTON EVENTS
        # ------------------------------
        run_btn.click(
            fn=run_full_analysis,
            inputs=[idea_a, model_name, temperature],
            outputs=[
                overview_report,
                analyzer_md,
                perspective_md,
                skeptic_md,
                severity_html,
                status_md,
            ],
        )

        # Also regenerate the debate view after analysis
        run_btn.click(
            fn=debate_view,
            inputs=[idea_a, model_name, temperature],
            outputs=debate_md,
        )

        compare_btn.click(
            fn=compare_ideas,
            inputs=[idea_a, idea_b, model_name, temperature],
            outputs=comparison_md,
        )

        return demo


if __name__ == "__main__":
    ui = create_ui()    # <— you were missing this line

    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

