<div align="center">

# 🪁 Kite
### Four-Eyes Principle for Autonomous SecOps Teammates
**Turning solo coding agents into a governed, human-in-the-loop security squad inside Switch Rooms.**

[![Built for Flip the Switch Hackathon](https://img.shields.io/badge/Flip_the_Switch-Hackathon_2026-6C5CE7?style=for-the-badge&logo=rocket)](https://www.wemakedevs.org/hackathons/switch)
[![Switch Protocol](https://img.shields.io/badge/Orchestrated_by-Switch_Rooms-00CEC9?style=for-the-badge)](https://switchagents.ai)
[![Models](https://img.shields.io/badge/Models-GPT--6--Luna_%7C_Gemini--3.1--Flash--Lite-FD79A8?style=for-the-badge)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-0984E3?style=for-the-badge)](LICENSE)

<br/>

> **Track:** Track 01: Best Business Workflow  
> **Core Thesis:** Engineering teams do not let autonomous AI agents near production because agents lack accountability, separation of duties, and hard governance. Kite implements the SOC **Four-Eyes Principle** inside Switch Rooms: specialized agents scout, validate, and remediate, but **no irreversible action can execute without verified human sign-off enforced at the tool layer**.

</div>

---

## 🎯 The Core Thesis: Why AI SecOps Needs the Four-Eyes Principle

Autonomous agent demos often show bots running unchecked scripts against staging servers. In real enterprise environments, unconstrained agents are dangerous:
1. **Lack of Separation of Duties**: A single agent writing a fix should never be allowed to verify its own work or deploy it unchecked.
2. **The Prompt-Gate Fallacy**: System prompts and keyword parsers are soft boundaries that can be bypassed by prompt injection or model hallucination.
3. **Operational Fear**: Teams keep agents out of production because they cannot guarantee that a rogue command (`rm -rf` or invalid WAF rule) won't take down legitimate customer traffic.

### Kite's Answer: SOC Governance in a Switch Room
Kite structures autonomous security operations around the classic **Four-Eyes Principle**:
* **Separation of Duties**: `@attacker` can only probe scoped sandboxes; `@fix-engine` cannot verify its own patches.
* **Independent Model Auditing**: `@verifier` runs on a distinct model architecture (`gemini-3.1-flash-lite` vs `gpt-6-luna`), ensuring zero cross-model confirmation bias.
* **Hard Tool-Layer Approval Gates**: High-risk actions (`apply_virtual_shield`, `create_github_pr`) require a single-use, cryptographically bound `plan_hash` signed off by a human lead. Direct tool invocations without human approval are blocked at the Python function layer.
* **Shared, Append-Only Room Log**: Switch provides the persistent multi-agent workspace where humans and agents collaborate, preserving an immutable log of what was proposed, who approved it, and when actions occurred.

---

## 🛠️ Complete Setup & Operations Guide (Zero to Production)

This guide walks you through every prerequisite, command, and configuration variable required to run Kite locally or deploy it to a cloud server (AWS EC2 / Linux).

### 📋 Prerequisites
- **Docker & Docker Compose (v2.20+)**: Required to run the multi-service containerized stack.
- **Python 3.11+**: Optional on host (all runtime execution occurs inside containers), but required if running unit tests locally.
- **Git (v2.30+)**: For source code cloning and GitOps repository inspection.

---

### 1️⃣ Clone the Repository & Enter Workspace

```bash
# Clone the complete Kite multi-agent codebase from GitHub
git clone https://github.com/yash-pouranik/kite.git

# Navigate into the project root directory
cd kite
```
> **What this does:** Downloads the entire Kite codebase, Dockerfiles, database migrations, security tool sandboxes, and automated test suites to your machine.

---

### 2️⃣ Initialize Environment Configuration

```bash
# Create your local environment file from the fully-documented template
cp .env.example .env
```
> **What this does:** Generates `.env`, which Docker Compose and the Python runtime automatically discover and inject into the runtime environment.

---

### 🔑 Complete Environment Variables Reference

Every single environment variable in `.env` is explained below with its purpose, default behavior, and where to obtain credentials:

#### A. LLM Provider Credentials (Cognitive Brains)

| Variable | Required | Default | Why it exists (Purpose) | Where to get it (Source) |
|:---|:---:|:---:|:---|:---|
| `OPENAI_API_KEY` | **Yes** | *None* | Powers deep reasoning, ethical exploit verification (`@attacker`), DevSecOps code remediation, and GitHub PR formatting (`@fix-engine`). | [OpenAI API Keys Portal](https://platform.openai.com/api-keys). Create a secret key with model access. |
| `GOOGLE_AI_API_KEY` | **Yes** | *None* | Powers ultra-low latency terminal log parsing (`@recon-bot`) and independent multi-model regression auditing (`@verifier`). | [Google AI Studio](https://aistudio.google.com/app/apikey). Generate a Gemini API key. |

#### B. Pinned AI Models & Execution Controls

| Variable | Required | Default | Why it exists (Purpose) | Where to get it (Source) |
|:---|:---:|:---:|:---|:---|
| `RECON_MODEL` | No | `gemini-3.1-flash-lite` | Pinned low-latency Google model for rapid scanner output parsing without hallucination. | Managed internally; change only if testing other Google GenAI models. |
| `ATTACKER_MODEL` | No | `gpt-6-luna` | Pinned high-reasoning OpenAI model for formulating safe, non-destructive proof-of-concept probes. | Managed internally; change only if evaluating alternative OpenAI models. |
| `FIX_ENGINE_MODEL` | No | `gpt-6-luna` | Pinned model for dual-track virtual shielding and clean Git patch synthesis. | Managed internally. |
| `VERIFIER_MODEL` | No | `gemini-3.1-flash-lite` | Distinct model family ensuring zero cross-model confirmation bias during regression audits. | Managed internally. |
| `MAX_TOOL_ITERATIONS` | No | `10` | Caps sequential tool hops per incident turn (prevents infinite tool loops while allowing deep multi-step chains). | Integer value (e.g. `10` or `12`). Set higher if chaining extensive recon + scan + PR workflows. |

#### C. Discord & Switch Integration

| Variable | Required | Default | Why it exists (Purpose) | Where to get it (Source) |
|:---|:---:|:---:|:---|:---|
| `DISCORD_BOT_TOKEN` | **Yes** | *None* | Connects Kite to your team Discord server so `@CyberWar-Room` can receive room messages and post agent replies. | [Discord Developer Portal](https://discord.com/developers/applications) ➡️ Select/Create App ➡️ **Bot** tab ➡️ Click **Reset Token** ➡️ Enable **Message Content Intent**. |
| `DISCORD_APP_APPLICATION_ID` | No | *None* | Discord Application ID for slash commands and bot identity validation. | Discord Developer Portal ➡️ **General Information** tab ➡️ Application ID. |
| `DISCORD_APP_CLIENT_SECRET` | No | *None* | Discord Client Secret for OAuth2 integrations. | Discord Developer Portal ➡️ **OAuth2** tab ➡️ Client Secret. |
| `SWITCH_SERVER_URL` | No | `http://switch-server:8000` | Address of the Switch Core bridge server where room events and WebSocket streams originate. | In Docker, points to internal service `http://switch-server:8000`. If running locally, `http://localhost:8000`. |
| `SWITCH_AGENT_REGISTRATION_TOKEN` | No | `secops-switch-token-2026` | Secret bootstrap token used by Kite to authenticate and auto-register with Switch Server. | Choose any 16+ char secret string, or copy from Switch Console Settings ➡️ API Keys. |
| `SWITCH_AGENT_ID` | No | `kite-secops` | Unique identity handle for Kite in Switch Rooms. | Set to any custom agent slug matching `^[a-z0-9][a-z0-9._-]*$`. |
| `SWITCH_AGENT_API_KEY` | No | *None* | Pre-issued agent API key from Switch Gateway (if manually provisioned). | Optional; if left blank, Kite auto-registers using `SWITCH_AGENT_REGISTRATION_TOKEN`. |
| `SWITCH_ROOM_ID` | No | `cyberwar-ops` | The target Switch Room name / Discord channel where the squad collaborates. | Enter your Discord channel name (e.g. `cyberwar-ops` or `secops-war-room`). |
| `SWITCH_ADMIN_EMAIL` | No | `admin@kite-secops.local` | Initial admin account email for the self-hosted Switch Gateway web dashboard. | Any valid email address you want to use for admin login. |
| `SWITCH_ADMIN_PASS` | No | `SecOpsAdminPass2026!` | Admin password for the Switch Gateway web dashboard (port 3000). | Choose a strong password (minimum 8 characters). |
| `SWITCH_SECRET_KEYS` | No | `k1:secops_master_...` | Master encryption and signing key for Switch Server state. | Format `<id>:<secret>`. Secret must be at least 32 characters long. |

#### D. Target Application & Infrastructure (100% Generic & Configurable)

| Variable | Required | Default | Why it exists (Purpose) | Where to get it (Source) |
|:---|:---:|:---:|:---|:---|
| `TARGET_HOST` | **Yes** | `target-app` | Domain, hostname, or IP of the target application to scan, profile, and defend with virtual shields. | Domain of your target app (e.g. `vynn.urbackend.in` or `staging.yourcompany.com`). |
| `HOST_REPO_PATH` | **Yes** | `/path/to/target/repository` | Path on the host machine containing target source code (mounted into container for native Git & SAST analysis). | Absolute local path to target repository (e.g. `/home/ubuntu/mcp-gateway-k8s` or `D:/projects/my-app`). |
| `K8S_NAMESPACE` | No | `default` | Kubernetes namespace inspected by `@recon-bot` and `kubectl` log forensics tools. | Kubernetes namespace of your target microservices (e.g. `gateway` or `default`). |

#### E. Real GitHub GitOps Integration

| Variable | Required | Default | Why it exists (Purpose) | Where to get it (Source) |
|:---|:---:|:---:|:---|:---|
| `GITHUB_TOKEN` | Optional* | *None* | Required for `create_github_pr` to branch, commit code fixes, and open real Pull Requests. | [GitHub Personal Access Tokens](https://github.com/settings/tokens) (Tokens classic) ➡️ Generate new token with **`repo`** scope. |
| `GITHUB_REPO_OWNER` | Optional* | *None* | GitHub user or organization owning the target repository. | Your GitHub username or organization (e.g. `yash-pouranik`). |
| `GITHUB_REPO_NAME` | Optional* | *None* | GitHub repository name receiving GitOps remediation PRs. | Target repository name (e.g. `mcp-gateway-k8s`). |

*\* Note: GitHub credentials are only required if you want Kite to open live Pull Requests on GitHub. All other recon, scanning, and virtual shielding tools work without it.*

#### F. Persistent Storage & Logging

| Variable | Required | Default | Why it exists (Purpose) | Where to get it (Source) |
|:---|:---:|:---:|:---|:---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | No | `secops` / `secops_secure_pass` | Database user and password for PostgreSQL persistent incident storage. | Keep defaults or set your own secure credentials. |
| `DATABASE_URL` | No | `postgresql://...` | Connection string used by FastAPI backend to persist incident audit trails and knowledge bases. | Standard PostgreSQL connection URL. |
| `REDIS_URL` | No | `redis://redis:6379/0` | Ephemeral memory cache, tool queue, and distributed session lock for multi-agent execution. | Standard Redis connection URL. |
| `ENVIRONMENT` | No | `development` | Runtime environment flag (`development` or `production`). | Set to `production` on live deployments. |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`INFO` for standard output, `DEBUG` for deep troubleshooting). | Standard Python log level. |

---

### 3️⃣ Build and Launch the Stack

Run the following command to build and start the entire multi-container workforce:

```bash
docker compose up -d --build
```

#### What this command does step-by-step:
1. **Builds `kite-gateway`**: Compiles the FastAPI multi-agent runtime, installs all Python dependencies (`websockets`, `openai`, `google-genai`, `httpx`, `discord.py`), registers the 30 DevSecOps tools, and installs `kubectl` CLI.
2. **Starts `kite-postgres`**: Spins up PostgreSQL 16 Alpine, creates the `cyberwar` database, and executes schema migration scripts (`001_initial.sql`).
3. **Starts `kite-redis`**: Initializes Redis 7 Alpine for sub-millisecond session memory and distributed locks.
4. **Builds `kite-sec-tools`**: Assembles the sandboxed security container with Nmap and Nuclei CLI binaries.
5. **Connects `secops-net`**: Creates an isolated Docker bridge network connecting all services with internal DNS resolution.
6. **Backgrounds Services (`-d`)**: Detaches the process so containers run persistently in the background.

---

### 4️⃣ Verify System Health & Endpoints

Run these commands to confirm that every component is fully operational:

```bash
# 1. Check container runtime status (all containers should show 'Up')
docker compose ps

# 2. Probe Kite Gateway Health Endpoint
curl http://localhost:8000/health
```
> **Expected Output:**
> ```json
> {
>   "status": "healthy",
>   "service": "Kite Autonomous SecOps Gateway",
>   "models": {
>     "recon_bot": "gemini-3.1-flash-lite",
>     "attacker": "gpt-6-luna",
>     "fix_engine": "gpt-6-luna",
>     "verifier": "gemini-3.1-flash-lite"
>   }
> }
> ```

```bash
# 3. Probe Switch Rooms Protocol & Bridge Status
curl http://localhost:8000/switch/status
```
> **Expected Output:**
> ```json
> {
>   "status": "online",
>   "room_id": "cyberwar-ops",
>   "agent_id": "kite-secops",
>   "protocol": "Official Switch Agent Protocol (WebSocket + HTTP)"
> }
> ```

```bash
# 4. Run the 12/12 Automated Test Suite
pytest tests/test_tools.py -v
```
> **What this does:** Executes all 12 unit tests verifying GitOps, SAST, secret detection, OSV dependency analysis, real GitHub PR auth, governed terminal execution, Switch WebSocket heartbeat, Tool-layer Four-Eyes approval gates, and adversarial refusal parsers.

---

### 5️⃣ Essential Maintenance & Management Commands

| Action | Command | What it does |
|:---|:---|:---|
| **View Live Agent Logs** | `docker compose logs -f gateway` | Streams live multi-turn reasoning logs, tool invocations, and Discord messages in real time. |
| **Hot Reload Gateway** | `docker compose restart gateway` | Restarts the Kite Agent gateway in under 2 seconds without wiping database state. |
| **Rebuild on Code Pull** | `docker compose up -d --build gateway` | Recompiles Python packages and syncs code updates after running `git pull origin main`. |
| **Inspect PostgreSQL Data** | `docker compose exec postgres psql -U secops -d cyberwar` | Opens an interactive SQL prompt inside the persistent database. |
| **Graceful Shutdown** | `docker compose down` | Stops and removes all containers while keeping database and redis volumes (`pgdata`, `redisdata`) 100% intact. |

---

## 🏗️ Architecture & Interaction Flow

```
                               ┌────────────────────────────────────────────────────────┐
                               │             DISCORD / SWITCH ROOM                      │
                               │  Human Lead + @recon-bot + @attacker + @fix + @verify │
                               └───────────────────────────▲────────────────────────────┘
                                                           │
                                        Switch Agent Protocol (WebSocket / HTTP)
                                        Shared, Append-Only Multi-Turn Room Log
                                                           │
  ┌────────────────────────────────────────────────────────▼────────────────────────────────────────────────────────┐
  │                                   KITE MULTI-AGENT GOVERNANCE GATEWAY                                           │
  │                                                                                                                  │
  │  ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐  │
  │  │   1. RECON-BOT       │    │   2. ATTACKER        │    │   3. FIX ENGINE      │    │   4. VERIFIER        │  │
  │  │  gemini-3.1-flash    │───▶│     gpt-6-luna       │───▶│     gpt-6-luna       │───▶│  gemini-3.1-flash    │  │
  │  │  Scans & Profiling   │    │  Safe PoC Validator  │    │  Dual-Remediation    │    │  Dual-Path Audit     │  │
  │  └──────────────────────┘    └──────────────────────┘    └──────────────────────┘    └──────────────────────┘  │
  │              │                          │                            │                           │               │
  │              ▼                          ▼                            ▼                           ▼               │
  │     [Nmap + Nuclei CLI]        [Harmless Read Probes]      [Hard Tool Approval Gate]   [200 OK vs 403 Audit]     │
  └──────────────┬──────────────────────────┬────────────────────────────┬───────────────────────────┬───────────────┘
                 │                          │                            │                           │
                 ▼                          ▼                            ▼                           ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                 TARGET ENVIRONMENT (vynn.urbackend.in)                                          │
  │          [Nginx Reverse Proxy / WAF] ─────────▶ [Kubernetes Pods / Namespace: gateway]                          │
  └──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 The 4 Specialized Roles & Model Matrix

| Agent Name | Model | Cognitive Role & Boundary |
|:---|:---|:---|
| **@recon-bot** | `gemini-3.1-flash-lite` | **Scout**: Ingests massive terminal logs, inspects repository manifests, runs SAST, and extracts CVEs with sub-second latency. |
| **@attacker** | `gpt-6-luna` | **Validator**: Formulates read-only verification probes (`' OR 1=1 --`) to eliminate false positives. Cannot touch fixes or production code. |
| **@fix-engine** | `gpt-6-luna` | **Remediation Architect**: Formulates Dual-Track Remediation (immediate virtual shield + permanent GitHub PR). Blocked from applying actions without human sign-off. |
| **@verifier** | `gemini-3.1-flash-lite` | **Independent QA Auditor**: Audits traffic before and after. Rejects flawed fixes if legitimate customer traffic is impacted. |

---

## 🛡️ Key Innovation: Dual-Track Remediation

When a high-severity vulnerability is confirmed, Kite executes a two-stage remediation strategy:

1. **Track 1: Immediate Zero-Downtime Virtual Shield (Hot WAF Rule)**
   - Injects a targeted regex rule into Nginx (`/etc/nginx/conf.d/patch_sqli.conf`).
   - Reloads Nginx dynamically (`nginx -s reload`) in 5ms.
   - Malicious attack signatures are blocked with `403 Forbidden` while legitimate traffic passes with `200 OK`.
2. **Track 2: Permanent Source Code Remediation (GitOps Pull Request)**
   - Automatically branches the repository, commits clean parameterized code, and opens a real GitHub PR.
   - Eliminates technical debt permanently so the virtual shield can be decommissioned safely.

---

## 🔒 Tool-Layer Four-Eyes Enforcement (Zero Bypasses)

Unlike systems that rely solely on system prompt instructions, Kite enforces human governance directly in the tool execution layer (`gateway/services/approval_guard.py`):

1. **Cryptographic Plan Binding**: Every proposed action registers a deterministic 12-char SHA-256 `plan_hash` bound to the action type, target endpoint, and parameters.
2. **Human-Only Sign-Off**: Bot and automated agent accounts attempting to call `approve_secops_plan` are strictly rejected.
3. **Single-Use & TTL Protection**: Approval tokens expire after 300 seconds and are immediately consumed upon execution, preventing replay attacks.
4. **Adversarial Refusal Parsing**: Negative qualifiers like *"don't deploy"*, *"approve nahi hai"*, *"why deploy?"*, and *"stop and wait"* are classified as `REFUSE_ACTION` and can never be misconstrued as approvals.

---

## ⚠️ Honest Boundaries & System Limitations

Senior engineering requires acknowledging technical boundaries:
- **Virtual Shields are Temporary**: Regex inspection filters stop active bleeding during an incident; they are not a substitute for proper parameterized source code and must always be superseded by the GitOps PR.
- **Terminal Execution Whitelist**: `execute_terminal_command` strictly blocks destructive commands (`rm -rf`, `shutdown`, `mkfs`) and secret file reads (`cat .env`) via hardcoded regex rules.
- **Human In the Loop**: High-risk actions require explicit human lead participation in the Switch Room. Kite will not unilaterally patch production without sign-off.

---

## 🧪 Automated Test Suite (12/12 Passing)

Every tool, security guardrail, and protocol handler is verified by our automated test suite:

```bash
pytest tests/test_tools.py -v
```
```text
tests/test_tools.py::TestSecOpsTools::test_01_tool_registry_registration PASSED [  8%]
tests/test_tools.py::TestSecOpsTools::test_02_git_operations PASSED      [ 16%]
tests/test_tools.py::TestSecOpsTools::test_03_code_sast_and_secrets PASSED [ 25%]
tests/test_tools.py::TestSecOpsTools::test_04_dependency_scanner PASSED  [ 33%]
tests/test_tools.py::TestSecOpsTools::test_05_local_test_runner PASSED   [ 41%]
tests/test_tools.py::TestSecOpsTools::test_06_real_pr_engine_no_mocks PASSED [ 50%]
tests/test_tools.py::TestSecOpsTools::test_07_governed_terminal_runner PASSED [ 58%]
tests/test_tools.py::TestSecOpsTools::test_08_switch_agent_protocol_client PASSED [ 66%]
tests/test_tools.py::TestSecOpsTools::test_09_tool_layer_four_eyes_approval_gate PASSED [ 75%]
tests/test_tools.py::TestSecOpsTools::test_10_adversarial_dialogue_refusals PASSED [ 83%]
tests/test_tools.py::TestSecOpsTools::test_11_pr_review_and_branch_manager_tools PASSED [ 91%]
tests/test_tools.py::TestSecOpsTools::test_12_k8s_kubeconfig_adaptation PASSED [100%]
============================= 12 passed in 35.87s =============================
```

---

## 🔧 Under the Hood: Centralized Tool Registry (30 Tools)

Kite exposes 30 type-safe tools across 7 operational domains via `gateway/tools/tool_registry.py`:
- **Governed Terminal**: Safe execution of `kubectl`, `git`, `docker`, `curl`, `npm`, `grep`. Destructive operations automatically blocked.
- **Kubernetes Forensics**: Live pod inspection (`get_k8s_pods`) and error log streaming (`tail_k8s_logs`) across target namespaces.
- **Native Git Operations**: Branch tracking, uncommitted diffs, and remote resolution (`get_git_status`, `get_git_diff`, `get_git_log`).
- **Code SAST & Secret Scanners**: AST pattern matching for raw SQL concatenation, disabled TLS/SSL, and high-entropy secret detection.
- **Dependency Security**: Live CVE analysis via OSV.dev REST API for `package.json` and `requirements.txt`.
- **GitOps PR Engine**: Real GitHub Pull Request automation with a Commit Diff Guarantee.
- **Active Remediation & Governance**: Virtual shield deployment, 1-click rollback, dual-path audit, and Four-Eyes plan approval (`approve_secops_plan`).

---

## ⚖️ Hackathon Judging Rubric Alignment

| Criteria | Weight | How Kite Delivers |
|:---|:---:|:---|
| **Use of Switch** | **30%** | **Load-Bearing Governance Hub**: Switch Rooms provide the shared, append-only conversation log, multi-agent identity separation, and human collaboration interface where the Four-Eyes Principle is enforced. Kite communicates natively via the official Switch Agent Protocol (WebSocket + HTTP Ingress). |
| **Technical Execution** | **25%** | **Deep Verification**: 30 native tools, live Kubernetes forensics (`kubectl`), real GitHub PRs with commit diff guarantee, tool-layer cryptographic approval gates, and 100% automated test coverage. |
| **Creativity & Impact** | **25%** | **Enterprise Problem Solved**: Replaces unconstrained AI agents with a governed SOC structure, providing zero-downtime virtual shielding alongside permanent code fixes. |
| **Presentation & Demo** | **20%** | **Real Production Target**: Tested live on AWS EC2 against Kubernetes pods (`vynn.urbackend.in`), featuring real approval gates and independent verifier scorecards. |

---

## 📜 License
Licensed under the MIT License. Built for the **Flip the Switch Hackathon (2026)**.
