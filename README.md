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

# Agent File Descriptions

- **example_agent.py**: A basic implementation demonstrating how to create and utilize an agent for classification tasks.
- **src/edge_answer_agent.py**: This agent generates answers for tasks that do not require repository changes and returns concise final answers directly.
- **src/edge_coding_agent.py**: An agent that handles tasks needing changes to the repository, generating the necessary file contents to apply changes and commit to the repository.
- **src/edge_coding_executor.py**: Implemented to execute tasks that involve repository coding, including cloning, changing branches, and applying code changes.
- **src/github_agent.py**: Responsible for interacting with GitHub repositories, including cloning or updating repositories and summarizing repository context.
- **src/json_utils.py**: Provides utility functions for parsing and handling JSON data within the application.
- **src/parser_agent.py**: Converts user-defined tasks into structured JSON for further processing by other agents.
- **src/repo_ops.py**: Implements operations for managing git repositories, such as applying file changes and committing to branches.
- **src/router_agent.py**: Evaluates tasks based on privacy, security, complexity, and latency to decide their execution routing.
- **src/supervisor.py**: Orchestrates the overall multi-agent workflow, connecting various agents to perform tasks systematically.