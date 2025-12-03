import os
from textwrap import dedent

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from agents.analyzer import run_analyzer
from agents.perspective import run_perspective_agent
from agents.skeptic import run_skeptic
from utils.combine import build_report, build_severity_bars
from utils.debate import build_debate_transcript

# ------------------------------
# ENV + CONFIG
# ------------------------------
load_dotenv(override=True)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

st.set_page_config(
    page_title="Blind Spot Finder — Multi-Agent Critical Reasoner",
    page_icon="🧠",
    layout="wide",
)



# ------------------------------
# CORE LOGIC (unchanged from Gradio version)
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
    """
    if not idea_a or not idea_a.strip():
        return (
            "⚠️ Please enter an idea, plan, or argument first.",
            "",
            "",
            "",
            "",
        )

    try:
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

        return (
            report,
            analyzer_out,
            perspective_out,
            skeptic_out,
            severity_html,
        )

    except Exception as e:
        err_msg = f"❌ Error during analysis: `{type(e).__name__}` — {e}"
        return (err_msg, "", "", "", "")


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


def compare_ideas(
    idea_a: str, idea_b: str, model_name: str, temperature: float
) -> str:
    if not idea_a or not idea_a.strip() or not idea_b or not idea_b.strip():
        return "⚠️ Please provide **both** Idea A and Idea B for comparison."

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "❌ OPENAI_API_KEY missing. Check your .env file or deployment secrets."

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
# STREAMLIT APP
# ------------------------------
def init_session_state():
    defaults = {
        "last_report": "",
        "last_analyzer": "",
        "last_perspective": "",
        "last_skeptic": "",
        "last_severity_html": "",
        "last_debate": "",
        "last_comparison": "",
        "history": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def main():
    init_session_state()

    st.markdown(
        """
        # 🧠 Blind Spot Finder — Multi-Agent Critical Reasoner  
        **Analyzer • Perspective • Skeptic Agents**

        Paste an idea, plan, argument, or product concept.  
        This system will attack it from multiple angles and surface hidden risks, assumptions, and missing perspectives.
        """
    )

    # ------------------------------
    # SIDEBAR — CONTROLS
    # ------------------------------
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        model_name = st.selectbox(
            "Model",
            ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
            index=["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"].index(DEFAULT_MODEL)
            if DEFAULT_MODEL in ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"]
            else 0,
        )

        temperature = st.slider(
            "Creativity (temperature)",
            min_value=0.0,
            max_value=1.0,
            value=0.4,
            step=0.05,
        )

        st.markdown("---")
        st.markdown("### 🔑 API Status")
        api_key_set = bool(os.getenv("OPENAI_API_KEY"))
        if api_key_set:
            st.success("OPENAI_API_KEY is set.")
        else:
            st.error("OPENAI_API_KEY is missing. Set it in your .env or deployment secrets.")

        st.markdown("---")
        st.markdown("### 🕒 Run History")
        if st.session_state["history"]:
            for i, item in enumerate(reversed(st.session_state["history"][-5:]), 1):
                st.markdown(f"**{i}.** {item[:80]}{'...' if len(item) > 80 else ''}")
        else:
            st.caption("No prior runs yet.")

    # ------------------------------
    # MAIN LAYOUT
    # ------------------------------
    col_left, col_right = st.columns([2, 1])

    with col_left:
        idea_a = st.text_area(
            "Primary Idea / Plan (Idea A)",
            height=200,
            placeholder="Example: I want to build an app that recommends playlists based on a user's mood...",
        )

    with col_right:
        idea_b = st.text_area(
            "Idea B (Optional, for comparison)",
            height=200,
            placeholder="Optional: second idea to compare against Idea A.",
        )

    col_buttons = st.columns([2, 2, 2])
    with col_buttons[0]:
        run_btn = st.button("🔍 Run Multi-Agent Analysis", use_container_width=True)
    with col_buttons[1]:
        compare_btn = st.button("⚖️ Compare Idea A vs Idea B", use_container_width=True)
    with col_buttons[2]:
        debate_btn = st.button("⚔️ Run Debate Only", use_container_width=True)

    status_placeholder = st.empty()

    # ------------------------------
    # ACTION HANDLERS
    # ------------------------------
    if run_btn:
        if not idea_a.strip():
            status_placeholder.warning("Please provide an idea for Analysis (Idea A).")
        else:
            status_placeholder.info("Running multi-agent analysis…")
            with st.spinner("Agents are thinking…"):
                (
                    report,
                    analyzer_md,
                    perspective_md,
                    skeptic_md,
                    severity_html,
                ) = run_full_analysis(idea_a, model_name, temperature)

                st.session_state["last_report"] = report
                st.session_state["last_analyzer"] = analyzer_md
                st.session_state["last_perspective"] = perspective_md
                st.session_state["last_skeptic"] = skeptic_md
                st.session_state["last_severity_html"] = severity_html
                st.session_state["last_debate"] = debate_view(
                    idea_a, model_name, temperature
                )

                st.session_state["history"].append(idea_a[:200])

            status_placeholder.success("✅ Multi-agent analysis complete.")

    if compare_btn:
        if not idea_a.strip() or not idea_b.strip():
            status_placeholder.warning("Please provide both Idea A and Idea B.")
        else:
            status_placeholder.info("Comparing Idea A vs Idea B…")
            with st.spinner("Comparing ideas…"):
                comparison_md = compare_ideas(idea_a, idea_b, model_name, temperature)
                st.session_state["last_comparison"] = comparison_md
            status_placeholder.success("✅ Comparison complete.")

    if debate_btn:
        if not idea_a.strip():
            status_placeholder.warning("Please provide an idea (Idea A) for debate.")
        else:
            status_placeholder.info("Generating debate transcript…")
            with st.spinner("Debate in progress…"):
                st.session_state["last_debate"] = debate_view(
                    idea_a, model_name, temperature
                )
            status_placeholder.success("✅ Debate generated.")

    # ------------------------------
    # TABS FOR OUTPUT
    # ------------------------------
    tab_overview, tab_agents, tab_debate, tab_comparison = st.tabs(
        ["📋 Overview Report", "🧬 Agent Outputs", "⚔️ Debate View", "⚖️ A vs B Comparison"]
    )

    with tab_overview:
        st.markdown("### Overview Report")
        if st.session_state["last_report"]:
            st.markdown(st.session_state["last_report"])
        else:
            st.caption("Run an analysis to see the report here.")

        st.markdown("### Blind Spot Severity Snapshot")
        if st.session_state["last_severity_html"]:
            st.components.v1.html(
                st.session_state["last_severity_html"],
                height=260,
                scrolling=False,
            )
        else:
            st.caption("Run an analysis to see the severity breakdown here.")

    with tab_agents:
        st.markdown("### Analyzer Agent")
        if st.session_state["last_analyzer"]:
            st.markdown(st.session_state["last_analyzer"])
        else:
            st.caption("Analyzer output will appear here.")

        st.markdown("---")
        st.markdown("### Perspective Agent")
        if st.session_state["last_perspective"]:
            st.markdown(st.session_state["last_perspective"])
        else:
            st.caption("Perspective output will appear here.")

        st.markdown("---")
        st.markdown("### Skeptic Agent")
        if st.session_state["last_skeptic"]:
            st.markdown(st.session_state["last_skeptic"])
        else:
            st.caption("Skeptic output will appear here.")

    with tab_debate:
        st.markdown("### Multi-Agent Debate Transcript")
        if st.session_state["last_debate"]:
            st.markdown(st.session_state["last_debate"])
        else:
            st.caption("Run an analysis or click 'Run Debate Only' to see a transcript.")

    with tab_comparison:
        st.markdown("### Idea A vs Idea B")
        if st.session_state["last_comparison"]:
            st.markdown(st.session_state["last_comparison"])
        else:
            st.caption("Provide both Idea A and Idea B, then click 'Compare'.")


if __name__ == "__main__":
    main()
    # ----------------------------------------------------
# 🔻 FOOTER WITH GITHUB + LINKEDIN
# ----------------------------------------------------
footer_html = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #0e1117;
    color: #cccccc;
    text-align: center;
    padding: 10px 0;
    font-size: 0.85rem;
    border-top: 1px solid #333;
}
.footer a {
    color: #4ea3ff !important;
    text-decoration: none;
    font-weight: 600;
}
.footer a:hover {
    color: #82c7ff !important;
    text-decoration: underline;
}
</style>

<div class="footer">
    Built by <strong>Nahom Melkamu</strong> — Blind Spot Finder © 2025  
    | <a href="https://github.com/Nahomworku1" target="_blank">GitHub</a>
    | <a href="https://www.linkedin.com/in/nahom-melkamu-worku-27b184299" target="_blank">LinkedIn</a>
</div>
"""

st.markdown(footer_html, unsafe_allow_html=True)

