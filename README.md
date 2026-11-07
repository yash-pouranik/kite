<div align="center">

# 🪁 Kite
### Four-Eyes Principle for Autonomous SecOps Teammates
**Turning solo coding agents into a governed, human-in-the-loop security squad inside Switch Rooms.**

[![Built for Flip the Switch Hackathon](https://img.shields.io/badge/Flip_the_Switch-Hackathon_2026-6C5CE7?style=for-the-badge&logo=rocket)](https://www.wemakedevs.org/hackathons/switch)
[![Switch Protocol](https://img.shields.io/badge/Orchestrated_by-Switch_Rooms-00CEC9?style=for-the-badge)](https://switchagents.ai)
[![Models](https://img.shields.io/badge/Models-GPT--6--Luna_%7C_Gemini--3.1--Flash--Lite-FD79A8?style=for-the-badge)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-0984E3?style=for-the-badge)](LICENSE)

<br/>

> **Track:** Track 01: Best Business Workflow ($2,000 Cash Prize)  
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

## 🧪 Automated Test Suite (11/11 Passing)

Every tool, security guardrail, and protocol handler is verified by our automated test suite:

```bash
pytest tests/test_tools.py -v
```
```text
tests/test_tools.py::TestSecOpsTools::test_01_tool_registry_registration PASSED [  9%]
tests/test_tools.py::TestSecOpsTools::test_02_git_operations PASSED      [ 18%]
tests/test_tools.py::TestSecOpsTools::test_03_code_sast_and_secrets PASSED [ 27%]
tests/test_tools.py::TestSecOpsTools::test_04_dependency_scanner PASSED  [ 36%]
tests/test_tools.py::TestSecOpsTools::test_05_local_test_runner PASSED   [ 45%]
tests/test_tools.py::TestSecOpsTools::test_06_real_pr_engine_no_mocks PASSED [ 54%]
tests/test_tools.py::TestSecOpsTools::test_07_governed_terminal_runner PASSED [ 63%]
tests/test_tools.py::TestSecOpsTools::test_08_switch_agent_protocol_client PASSED [ 72%]
tests/test_tools.py::TestSecOpsTools::test_09_tool_layer_four_eyes_approval_gate PASSED [ 81%]
tests/test_tools.py::TestSecOpsTools::test_10_adversarial_dialogue_refusals PASSED [ 90%]
tests/test_tools.py::TestSecOpsTools::test_11_pr_review_and_branch_manager_tools PASSED [100%]
============================= 11 passed in 6.69s ==============================
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

## 🛠️ Quickstart

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### 1. Clone & Configure
```bash
git clone https://github.com/yash-pouranik/kite.git
cd kite
cp .env.example .env
```
Configure your `.env` variables:
- `OPENAI_API_KEY`: API key for reasoning (`gpt-6-luna`).
- `GOOGLE_AI_API_KEY`: API key for fast parsing & independent auditing (`gemini-3.1-flash-lite`).
- `DISCORD_BOT_TOKEN`: Discord Bot Token for room collaboration.
- `GITHUB_TOKEN`: Personal Access Token for real GitOps Pull Requests.

### 2. Start Services
```bash
docker compose up -d
```
The gateway is available at `http://localhost:8000` with status monitored via `http://localhost:8000/switch/status`.

---

## 📜 License
Licensed under the MIT License. Built for the **Flip the Switch Hackathon (2026)**.
