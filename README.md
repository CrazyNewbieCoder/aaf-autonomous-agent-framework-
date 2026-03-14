# 🌌 Autonomous Agent Framework (AAF)

**AAF** is a full-fledged OS-level entity, an asynchronous AI agent, and a system administrator built on a microservice Event-Driven architecture.

While popular solutions (e.g., *OpenClaw*) bet on lightweightness, TypeScript, and storing logs in text files, **AAF is a heavyweight engineering framework in Python**. It is created for those who need complex graph memory, absolute isolation of executed code, and genuine proactivity.

Most modern Open-Source agents suffer from three problems: amnesia (forgetting context after 5 steps), looping (endless ReAct loops), and dependency hell during installation. **AAF solves them all.**

---
## 🔥 Architectural Features

*   **🧠 Triple Hybrid Memory (State-of-the-Art):** Unlike other frameworks that store memory in plain Markdown files or rely solely on vector search, the AAF system does not lose context. It combines Vector DB (ChromaDB: semantics and stream of consciousness), PostgreSQL (hard rules and long-term tasks), and a full-fledged **GraphRAG** based on KuzuDB (non-linear associations and agent intuition).

*   **⚡ Asynchronous Event Bus (EventBus):** The agent's brain is completely decoupled from the sensors. Instead of primitive Cron schedulers, messages from Telegram, system logs, and background tasks fall into a single priority queue. The agent decides what to react to right now and what to leave for later. The agent has 3 independent cycles: event reaction, proactivity, and introspection (reflection).

*   **🐝 Agent Swarm System & Docker Sandbox:** The main agent is an orchestrator of separate autonomous subagents. Need to analyze 500 pages of logs, gather a news digest from Habr, or test questionable Python code? The brain dynamically spawns specialized subagents and delegates the "dirty work" to them. 
    *   *Security:* AAF uses a **Docker-in-Docker** architecture. Every script is executed in a disposable, absolutely isolated Linux capsule. 
    *   *Agentic Mesh:* Subagents can pass tasks to each other like a baton, saving your expensive tokens and API quotas.

*   **👁️ Multimodality:** You can use any purely text-based model (e.g., GLM-5, Gemini, or Claude) as the main brain. If the agent receives a photo, sticker, or voice message, the system automatically passes the media through a dedicated Vision/Audio model (a sort of coprocessor) and returns a detailed text description to the main brain.

*   **🎭 Zero-Code Personality Customization:** To completely change the agent's character, you don't need to know Python. It is enough to edit 3 plain text files in the `config/personality` folder.

*   **💸 Free Operation (API Rotator):** The built-in key manager uses a Round-Robin algorithm. If one key hits the quota limit (429), the system imperceptibly switches to the next one.

*   **🛡️ WatchDog & Self-Healing:** If any system module crashes, the agent wakes up with maximum priority, reads the Traceback, analyzes its own source code, and tries to find a solution to the problem.

---
## 🏗 Project Structure
The project uses a strict `src-layout` for architectural cleanliness:

*   `src/` - The source code of the logic, divided into layers (Utils, Databases, Sensors, Brain, Swarm).
*   `workspace/` - Isolated zone. Here lie temporary files, the script sandbox (`sandbox`), and all databases (`_data`). **This folder is ignored by Git for the security of your data.**
*   `config/` - System settings and personality prompts.

---
## ⚙️ Installation (Quick Start)

No `pip install`, C++ compiler version conflicts, or manual database configuration. The entire project is packaged in Docker and deployed by an automatic script.

**Requirements:** Installed Docker Desktop and Python 3.11+ (only for running the startup script on the host).

### Step 1. Cloning

```bash
git clone https://github.com/th0r3nt/AAF-Autonomous-Agent-Framework-

cd AAF-Autonomous-Agent-Framework-
```

### Step 2. Initialization (First Run)

Run the installer. It will check dependencies and create the necessary folder structure.

```bash
python aaf_setup.py
```

The script will create a `.env` file. The script will stop and ask you to fill it out.

### Step 3. Key Configuration

Open the created `.env` file and enter your data there:

* `TG_API_ID_AGENT` and `TG_API_HASH_AGENT` (get at https://my.telegram.org/auth).
* `LLM_API_KEY_1` (up to 100 different ones are supported).
* `TAVILY_API_KEY` (for internet search).
* `OPENWEATHER_API_KEY` (weather).

### Step 4. Completing Installation
Run the script again:

```bash
python aaf_setup.py
```

The script will download NLP models (Sentence-Transformers) into the `workspace` folder and ask you to authorize the agent's Telegram account (enter phone number and code). Unlike bot tokens, AAF uses **MTProto (Telethon)** - the agent lives in Telegram as a real user.

### Step 4. settings.yaml
Next, you need to choose the agent's name and the model it will run on. Optionally, you can configure individual parameters: Max ReAct Steps, the length of the transmitted context, and so on.

### Step 5. Launch

```bash
docker compose up -d --build
```

That's it! Your agent will wake up, connect to Telegram, and begin proactively analyzing the system. You can view the logs with the command: `docker compose logs agent_core -f`.

### 🧠 Personality Customization
You can turn the agent into anyone: from a dry corporate analyst to a sarcastic AI from video games.

After running `aaf_setup.py`, 3 files will appear in the `config/personality/` folder:

* `SOUL.md` - The core of the personality (who they are, what they want, how they relate to the world).
* `COMMUNICATION_STYLE.md` - Speech rules (whether to use emojis, how to address people).
* `EXAMPLES_OF_STYLE.md` - Dialogue examples for setting up Few-Shot prompting.

Simply change the text in these files, save them, and the next time the agent wakes up, they will behave in a new way. You don't need to restart the container (context is assembled dynamically).

You can also configure the model, timeouts, and token limits in the `config/settings.yaml` file.

### ⚠️ Important Security Warning (Docker-in-Docker)

The AAF architecture uses Docker socket forwarding (`/var/run/docker.sock`) inside the `agent_core` container. This is necessary so that the agent can dynamically create isolated sandboxes (worker containers) to execute Python scripts.

What this means: The agent has administrator (root) rights over the Docker daemon of your host machine. Do not run the project on production servers with critical data without additional isolation. The project is intended for local launch (on a personal PC) or on a dedicated VPS.


## 🛠 Tech Stack

Core: Python 3.11+, Asyncio, Pydantic, Docker
Memory: PostgreSQL (SQLAlchemy + JSONB), ChromaDB (Vector), KuzuDB (Graph)
Sensors: Telethon (MTProto), psutil
LLM Engine: Support for any OpenAI-compatible models (Gemini, GPT, Claude, GLM, etc.).

You can also check out my Telegram channel - I talk more about development there. t.me/VEGA_and_other_heresy

*Architecture & Code by th0r3nt.*