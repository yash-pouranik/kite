<div align="center">

# 🪁 Kite
### Autonomous Multi-Agent SecOps Teammate Platform
**Turn your solo security tools into an autonomous War Room team.**

[![Built for Flip the Switch Hackathon](https://img.shields.io/badge/Flip_the_Switch-Hackathon_2026-6C5CE7?style=for-the-badge&logo=rocket)](https://www.wemakedevs.org/hackathons/switch)
[![Switch Protocol](https://img.shields.io/badge/Orchestrated_by-Switch_Rooms-00CEC9?style=for-the-badge)](https://switchagents.ai)
[![Models](https://img.shields.io/badge/Models-GPT--6--Luna_%7C_Gemini--3.1--Flash--Lite-FD79A8?style=for-the-badge)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-0984E3?style=for-the-badge)](LICENSE)

<br/>

> **Track:** Track 01: Best Business Workflow ($2,000 Cash Prize)  
> **Key Innovation:** Kite connects autonomous multi-model agents with human engineers in Discord using Switch Protocol to discover vulnerabilities, safely verify exploits, deploy zero-downtime virtual shields, and open permanent GitOps Pull Requests.

</div>

---

## 💡 The Problem: Alert Fatigue & Slow Remediation

Security operations today are broken:
1. **Alert Fatigue**: Automated scanners (Nmap, Nuclei, SonarQube) generate thousands of alerts. 85% are false positives, overwhelming human SecOps teams.
2. **Context Switching**: Engineers waste hours switching between terminal CLIs, cloud dashboards, Jira tickets, and Slack channels.
3. **The Remediation Dilemma**: Blocking a vulnerable API takes down business services (customer outage). Waiting for developers to rewrite code leaves companies exposed for an average of 42 days.

---

## 🚀 The Solution: Kite

Kite is an **Enterprise Cloud-Security Autonomous Workforce Platform**. It connects 4 specialized AI agents into a corporate **Discord War Room** using the open-source **Switch Protocol**:

```
                               ┌────────────────────────────────────────────────────────┐
                               │             DISCORD (Corporate War Room)               │
                               │  #incidents  #recon-feed  #attack-log  #remediation    │
                               └───────────────────────────▲────────────────────────────┘
                                                           │
                                              Switch Core Engine (Docker)
                                              SSE Inbound ↓ | HTTP POST Outbound ↑
                                                           │
 ┌─────────────────────────────────────────────────────────▼────────────────────────────────────────────────────────┐
 │                                   FASTAPI STATEFUL ORCHESTRATION GATEWAY                                         │
 │                                                                                                                  │
 │  ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐  │
 │  │   1. RECON-BOT       │    │   2. ATTACKER        │    │   3. FIX ENGINE      │    │   4. VERIFIER        │  │
 │  │  gemini-3.1-flash    │───▶│     gpt-6-luna       │───▶│     gpt-6-luna       │───▶│  gemini-3.1-flash    │  │
 │  │  Scans & Profiling   │    │  Safe PoC Validator  │    │  Dual-Remediation    │    │  Dual-Path Audit     │  │
 │  └──────────────────────┘    └──────────────────────┘    └──────────────────────┘    └──────────────────────┘  │
 │              │                          │                            │                           │               │
 │              ▼                          ▼                            ▼                           ▼               │
 │     [Nmap + Nuclei CLI]        [Harmless Read Probes]      [Nginx WAF + Git PR]        [200 OK vs 403 Audit]     │
 └──────────────┬──────────────────────────┬────────────────────────────┬───────────────────────────┬───────────────┘
                │                          │                            │                           │
                ▼                          ▼                            ▼                           ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                      ISOLATED TARGET RUNTIME NETWORK                                             │
 │          [Nginx Reverse Proxy / WAF] ─────────▶ [Kubernetes Pods / Microservices Staging App]                    │
 └──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 The 4 Specialized Agents & Multi-Model Matrix

We strategically assign models based on their core cognitive strengths:

| Agent Name | Model Assigned | Provider | Cognitive Role & Justification |
|:---|:---|:---|:---|
| **Recon-Bot** | `gemini-3.1-flash-lite` | Google | **Ultra-Low Latency Parser**: Ingests massive terminal logs from Nmap and Nuclei, extracting structured CVEs and ports in milliseconds. |
| **Attacker** | `gpt-6-luna` | OpenAI | **Deep Reasoning & Risk Modeling**: Formulates safe proof-of-concept verification probes to eliminate false positives without data loss. |
| **Fix Engine** | `gpt-6-luna` | OpenAI | **Principal DevSecOps Architect**: Formulates Dual-Track Remediation (Zero-Downtime Virtual Patch + Parameterized GitHub PR). |
| **Verifier** | `gemini-3.1-flash-lite` | Google | **Independent Quality Auditor**: Runs fast parallel regression tests to ensure legitimate customer traffic is 100% operational. |

---

## ⚡ Enterprise Tooling Architecture (28 Native Tools & Registry)

Kite provides a centralized, type-safe **`ToolRegistry`** providing 28 audited tools across 7 operational domains:

| Category | Native Tools | Real-World Capability |
|:---|:---|:---|
| **Governed Terminal** | `execute_terminal_command` | Executes arbitrary safe CLI commands (`kubectl`, `docker`, `git`, `curl`, `npm`, `grep`) under strict SecOps guardrails blocking destructive commands (`rm -rf`, `shutdown`) and `.env` secret leakage. |
| **Kubernetes Forensics** | `get_k8s_pods`, `tail_k8s_logs` | Inspects live Kubernetes microservices pods, readiness, and tails 500 error stack traces directly from cluster namespaces (e.g. `gateway`). |
| **Git Operations** | `get_git_remote_info`, `get_git_status`, `get_git_diff`, `get_git_log`, `get_git_branches` | Real repository visibility via native Git CLI; auto-detects remotes, inspects uncommitted diffs, and tracks commits without dubious ownership issues. |
| **Code SAST & Secrets** | `scan_codebase_sast`, `scan_codebase_secrets` | Static code analysis detecting raw SQL injection patterns, disabled TLS/SSL, eval, and high-entropy secret detection (AWS keys, OpenAI tokens, JWTs). |
| **Dependency Security (SCA)** | `scan_dependencies` | Queries live **OSV.dev REST API** against `package.json` and `requirements.txt` to identify known CVEs and safe upgrade versions. |
| **Real GitHub GitOps** | `create_github_pr`, `check_github_ci_status`, `sync_github_issue` | **100% Zero Mock Policy**: Opens real GitHub Pull Requests with a **Commit Diff Guarantee**, commits remediation audit notes, and queries CI status. |
| **Runtime Observability** | `tail_container_logs`, `check_service_health` | Probes live endpoint latency, status codes, and tails Docker runtime container logs. |
| **Active Remediation** | `apply_virtual_shield`, `rollback_virtual_shield`, `verify_dual_track_remediation` | Deploys zero-downtime Nginx WAF rules in 5ms, hot-reloads proxy, provides 1-Click Rollback, and conducts dual-track regression audits (200 OK vs 403 Forbidden). |

---

## 🛡️ Key Innovation: Dual-Track Remediation

When a critical vulnerability (e.g. SQL Injection) is confirmed, Fix Engine does **not** take down the service or blindly rewrite container files:

1. **Layer 1: Immediate Shield (Zero Downtime)**
   - Injects a targeted regex filter into Nginx (`/etc/nginx/conf.d/patch_sqli.conf`).
   - Hot-reloads Nginx (`nginx -s reload`) in milliseconds.
   - Malicious attack strings (`' OR 1=1`, `UNION SELECT`) are blocked with `403 Forbidden`.
   - **Legitimate customer traffic continues working with `200 OK`!**
2. **Layer 2: Permanent Fix (GitOps Pull Request)**
   - Automatically branches the application repository (`secops/fix-sqli-inc-101`).
   - Refactors raw string-concatenated SQL queries into safe parameterized statements.
   - Submits a GitHub Pull Request with before/after code diffs and vulnerability analysis.

---

## 🧪 Automated Testing & Verification

Every single tool, guardrail, and Git/Kubernetes operation is verified by an automated unit test suite:

```bash
python -m unittest tests/test_tools.py
```
```text
Ran 7 tests in 6.673s - OK
- test_01_tool_registry_registration (All 28 tools registered)
- test_02_git_operations (Status, logs, remotes, branches verified)
- test_03_code_sast_and_secrets (AST and Secret scanners verified)
- test_04_dependency_scanner (OSV.dev live CVE API verified)
- test_05_local_test_runner (Automated test suite execution verified)
- test_06_real_pr_engine_no_mocks (Strict auth enforcement verified)
- test_07_governed_terminal_runner (Safe commands allowed, rm -rf and .env blocked)
```

---

## ⚖️ Hackathon Judging Rubric Alignment

| Criteria | Weight | How Kite Wins |
|:---|:---:|:---|
| **Use of Switch** | **30%** | **Fundamental to Architecture**: Switch's multi-agent room infrastructure is the entire backbone. Agents share state, track human confirmations, and collaborate in Discord. Without Switch, this system does not exist. |
| **Technical Execution** | **25%** | **Deep Engineering**: 28 native tools, Kubernetes pod forensics (`kubectl`), Governed Terminal runner, live OSV.dev SCA, hot-reloadable Nginx reverse proxy, real GitHub PRs with commit diff guarantee. |
| **Creativity & Impact** | **25%** | **Real-World Societal & Business Impact**: Tackles alert fatigue and the \$4.5M average cost of data breaches. Introduces dual-remediation so businesses stay secure without outages. |
| **Presentation & Demo** | **20%** | **Compelling Live Story**: Complete end-to-end simulation script, rich Discord markdown embeds, objective verification scorecards, and reproducible setup. |

---

## 🛠️ Quickstart (Running Locally in 5 Minutes)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed & running.
- Python 3.11+.

### 1. Clone the Repository
```bash
git clone https://github.com/yash-pouranik/kite.git
cd kite
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
Fill in your required credentials in `.env`:
- `DISCORD_BOT_TOKEN`: **(Mandatory)** Your Discord Bot Token (connects Switch to your Discord server channels).
- `OPENAI_API_KEY`: **(Mandatory)** Your OpenAI API key (for `gpt-6-luna`).
- `GOOGLE_AI_API_KEY`: **(Mandatory)** Your Google Gemini API key (for `gemini-3.1-flash-lite`).
- `GITHUB_TOKEN`: (Optional) GitHub Personal Access Token if testing live PR creation against a real repository.

### 3. Start the Complete Infrastructure Stack
```bash
docker compose up -d
```

---

## 📜 License & Credits

Built with ❤️ by Solo Builder for the **Flip the Switch Hackathon (2026)** organized by **WeMakeDevs × DevTools Academy × Switch**.  
Licensed under the MIT License.
