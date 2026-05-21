# EdgeCloud-cse599
This project implements a multi-agent workflow that dynamically evaluates programming tasks and determines whether they should execute on edge devices or in the cloud based on factors such as privacy, latency, security. After making a deployment decision, the system automatically routes and executes the task in the selected environment.


# Setup Instructions

## 1. Clone the repository

```bash
git clone https://github.com/AnikaAru/EdgeCloud-cse599.git
cd EDGECLOUD-CSE599
```

---

## 2. Install uv

```bash
pip install uv
```

Verify installation:

```bash
uv --version
```

---

## 3. Create virtual environment

```bash
uv venv
```

---

## Activate the environment

Windows

```powershell
.venv\Scripts\activate
```

Mac/Linux
```bash
source .venv/bin/activate
```
---

## 4. Install dependencies

```bash
uv pip install langgraph langchain langchain-openai langsmith python-dotenv
uv pip install "langgraph-cli[inmem]"
```

---

## 5. Create `.env`

Copy the example environment file 

### Mac/Linux

```bash
cp .env.example .env
```

Fill in your API keys for OPENROUTER and LANGSMITH

---

# Links to get API Keys

## OpenRouter

Set monthly spend limit to $10

https://openrouter.ai/

## LangSmith

https://smith.langchain.com/

---

# Running the Project

## Run locally

```bash
uv run python main.py
```

---

## Run LangGraph Studio

```bash
uv run langgraph dev
```

This launches:
- local LangGraph server
- LangGraph Studio
- LangSmith tracing

The terminal will output a Studio URL.
Click on the studio url to see the agent graphs and traces in langsmith 
---

# Notes
- `.env` should NEVER be committed
