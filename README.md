
# 🌌 Autonomous Agent Framework (AAF)

**AAF** is a full-fledged OS-level entity, an asynchronous AI agent, and a multi-agent platform built on a microservice Event-Driven architecture.

While popular solutions bet on lightweightness, TypeScript, and storing logs in text files, **AAF is a heavyweight engineering framework in Python**. It is created for those who need complex graph memory, absolute isolation of executed code, and genuine proactivity.

Most modern Open-Source agents suffer from three problems: amnesia (forgetting context after 5 steps), looping (endless ReAct loops), and dependency hell during installation. **AAF solves them all.**

---

## 📚 Documentation (Deep Dive)
Detailed architecture descriptions and guides are available in the `docs/` folder (currently in Russian):
* 🏗️ [Core Anatomy & EventBus](docs/ARCHITECTURE_RU.md)
* 🧠 [Triple Hybrid Memory (GraphRAG)](docs/MEMORY_AND_GRAPH_RU.md)
* 🐝 [Agent Swarm System](docs/SWARM_SYSTEM_RU.md)
* 🧩 [Plugins Guide (Zero-Boilerplate)](docs/PLUGINS_GUIDE_RU.md)
* 🎭 [Personality Tuning](docs/PERSONALITY_TUNING_RU.md)
* 🚑 [Troubleshooting](docs/TROUBLESHOOTING_RU.md)

---

## 🔥 Key Features (Briefly)

* **♾️ Multi-Agent CLI Manager:** Deploy and orchestrate any number of independent agents on a single server via an interactive terminal (`aaf.py`). Docker Compose is generated automatically.
* **🧠 Triple Hybrid Memory (SOTA):** The agent does not lose context. A combination of SQL (hard rules), ChromaDB (semantics), and full-fledged **GraphRAG** based on KuzuDB (non-linear associations).
* **⚡ Asynchronous Event Bus (EventBus):** The brain is completely decoupled from the sensors. Messages from Telegram, system logs, and background tasks fall into a single priority queue.
* **💸 Free Operation (API Rotator):** The built-in key manager uses a Round-Robin algorithm and automatically switches to the next API key when limits are reached (429 error).
* **🛡️ Code Isolation (True DinD):** If the agent writes code, it is executed in disposable, fully isolated Docker containers inside a sandbox. Your host OS is 100% safe.

---

## ⚙️ Installation (Quick Start)

No `pip install`, C++ compiler version conflicts, or manual database configuration. The project is packaged in Docker.
**Requirements:** Installed Docker Desktop and Python 3.11+ (only for running the CLI manager).

### Step 1. Clone the Repository
```bash
git clone https://github.com/th0r3nt/AAF-Autonomous-Agent-Framework-
cd AAF-Autonomous-Agent-Framework-
```

### Step 2. Create an Agent Profile
Launch the interactive manager:
```bash
python aaf.py
```
Inside the console, enter the creation command (e.g., `LUMI`):
```text
create LUMI
```
*The script will generate the `Agents/LUMI/` folder structure, settings, and prepare Docker.*

### Step 3. Configure Keys
Open the newly created `Agents/LUMI/.env` file and enter:
* `TG_API_ID_AGENT` and `TG_API_HASH_AGENT` (get at [my.telegram.org](https://my.telegram.org/auth)).
* `LLM_API_KEY_1` (any number of keys are supported).

### Step 4. Telegram Authorization
In the AAF console, enter:
```text
auth LUMI
```
The script will ask for a phone number and a code. AAF uses **MTProto (Telethon)** — the agent lives in Telegram as a real user.

### Step 5. Launch
In the AAF console, enter:
```text
start LUMI
```
That's it! Docker will download the images, spin up the databases, and start the agent. View beautiful logs using `logs LUMI`.

---

## 🧩 Extensibility: Plugins vs Sandbox

AAF provides two code execution mechanisms:

1. **Sandbox (Routine Level):** The agent *autonomously* writes a Python script and sends it to the isolated `sandbox_engine`. 100% isolation. Ideal for disposable scraping or math.
2. **Plugins/Skills (Brain Level):** You (the human) write a `.py` file in `Agents/<NAME>/plugins/`, apply the `@llm_skill` decorator, and the framework automatically generates the JSON schema for OpenAI Tools. 0% isolation, direct core access. [Read the Plugins Guide](docs/PLUGINS_GUIDE_RU.md).

---

## 🛠 Tech Stack

* **Core:** Python 3.11+, Asyncio, Pydantic, Docker.
* **Memory:** PostgreSQL (SQLAlchemy + JSONB), ChromaDB (Vector), KuzuDB (Graph).
* **Sensors:** Telethon (MTProto), psutil.
* **LLM Engine:** Any OpenAI-compatible API (Gemini, GPT, Claude, DeepSeek, etc.).

Author's Telegram channel: [t.me/VEGA_and_other_heresy](https://t.me/VEGA_and_other_heresy)  
*Architecture & Code by th0r3nt.*
```