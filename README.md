🧠 Blind Spot Finder — Multi-Agent Critical Reasoner

Analyzer • Perspective • Skeptic Agents

The Blind Spot Finder is a multi-agent reasoning system built to uncover hidden assumptions, unseen risks, and structural weaknesses in any idea, plan, argument, or proposal.
Instead of giving friendly answers, it attacks your idea from multiple angles using specialized agents — then produces a structured blind-spot report.

🔗 Live Demo: https://blind-spot-finder.onrender.com

🔗 Source Code: https://github.com/Nahomworku1/blind_spot_finder

🚀 What This System Does

Three specialized agents analyze the user’s idea:

Analyzer Agent → surfaces missing logic, flawed assumptions, and weak spots.

Perspective Agent → reframes the idea through alternate expert viewpoints.

Skeptic Agent → aggressively stress-tests the idea and exposes failure modes.

All results are merged into a single, clean, useful blind-spot report.

🔧 Features

Multi-agent reasoning (Analyzer / Perspective / Skeptic)

Structured blind-spot analysis

Multi-agent debate mode

Idea A vs B comparison mode

Severity heatmap visualization

Modern Streamlit interface

Easy deployment on Render

Modular prompts & code structure

🧠 How It Works (Short Version)

You enter an idea — small or big.

Each agent evaluates it from a different cognitive style.

A debate simulation runs between the agents.

A final blind-spot report is generated.

You receive:

key risks

hidden assumptions

contradictions

alternative perspectives

worst-case scenarios

improvement suggestions

Example Input:

"I want to build an AI therapist that diagnoses depression."

Output Highlights:

Medical safety issues

Legal barriers

Ethical constraints

Misdiagnosis risk

Bias problems

Regulatory concerns

📁 Project Structure
blind_spot_finder/
│
├── agents/
│   ├── analyzer.py
│   ├── perspective.py
│   └── skeptic.py
│
├── utils/
│   ├── combine.py
│   └── debate.py
│
├── prompts/
│   ├── analyzer_prompt.txt
│   ├── perspective_prompt.txt
│   ├── skeptic_prompt.txt
│   └── report_template.txt
│
├── examples/
│   ├── example_input.txt
│   └── example_output.txt
│
├── sl_app.py
├── requirements.txt
└── README.md

⚙️ QuickStart (Local)
git clone https://github.com/Nahomworku1/blind_spot_finder
cd blind_spot_finder
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt


Create a .env file:

OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini


Run the app:

streamlit run sl_app.py

🌐 Deploy on Render

Build Command:

pip install -r requirements.txt


Start Command:

streamlit run sl_app.py --server.port=$PORT --server.address=0.0.0.0

🧪 Sample Prompts to Demonstrate the System

These produce extremely strong and impressive analyses:

1. AI Therapist

“I want to build an AI therapist that replaces human therapists…”

2. AI TikTok with AI influencers

“I want to build a TikTok competitor using AI influencers…”

3. AGI managing governments

“I want AGI to manage national governments…”

4. Digital nomad life decision

“I want to move to another country with no savings…”

5. Automated coding multi-agent system

“I want to build an AI that writes, tests, deploys code automatically…”

(Full prompt list available on request.)

📚 Resources

👉 GitHub Repo:
https://github.com/Nahomworku1/blind_spot_finder

👉 Live App:
https://blind-spot-finder.onrender.com

👉 Examples Folder:
/examples

👉 Documentation:
See README + comments in code

👤 Author

Nahom Melkamu Worku
🔗 LinkedIn: https://www.linkedin.com/in/nahom-melkamu-worku-27b184299/

🔗 GitHub: https://github.com/Nahomworku1

⭐ License

MIT License — free for personal & commercial use.
