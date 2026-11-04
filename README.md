<div align="center">

# 🪁 Kite
### Autonomous Multi-Agent SecOps Teammate Platform
**Turn your solo security tools into an autonomous War Room team.**

[![Built for Flip the Switch Hackathon](https://img.shields.io/badge/Flip_the_Switch-Hackathon_2026-6C5CE7?style=for-the-badge&logo=rocket)](https://www.wemakedevs.org/hackathons/switch)
[![Switch Protocol](https://img.shields.io/badge/Orchestrated_by-Switch_Rooms-00CEC9?style=for-the-badge)](https://switchagents.ai)
[![Models](https://img.shields.io/badge/Models-GPT--6--Luna_%7C_Gemini--3.1--Flash--Lite-FD79A8?style=for-the-badge)](https://openai.com)
[![License](https://img.shields.io/badge/License-Apache_2.0-0984E3?style=for-the-badge)](LICENSE)

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
 │          [Nginx Reverse Proxy / WAF] ─────────▶ [OWASP Juice Shop / Staging App Container]                       │
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

## 🛡️ Key Innovation: Dual-Track Remediation

When a critical vulnerability (e.g. SQL Injection) is confirmed, Fix Engine does **not** take down the service or blindly rewrite container files:

1. **Layer 1: Immediate Shield (Zero Downtime)**
   - Injects a targeted regex filter into Nginx (`/etc/nginx/conf.d/patch_sqli.conf`).
   - Hot-reloads Nginx (`nginx -s reload`) in milliseconds.
   - Malicious attack strings (`' OR 1=1`, `UNION SELECT`) are blocked with `403 Forbidden`.
   - **Legitimate shopper traffic (`apple`, `mug`) continues working with `200 OK`!**
2. **Layer 2: Permanent Fix (GitOps Pull Request)**
   - Automatically branches the application repository (`secops/fix-sqli-inc-101`).
   - Refactors raw string-concatenated SQL queries into safe parameterized statements.
   - Submits a GitHub Pull Request with before/after code diffs and vulnerability analysis.

---

## 💬 Natural Language Conversational Experience

No rigid CLI commands (`@recon-bot scan target:juice-shop`). Human engineers talk naturally:

```text
Alex (SecOps Lead): "Hey team, could someone check our store app for any security holes?"

Recon-Bot: "Good morning Alex! I noticed you'd like a security audit. 
Which environment should I profile (our internal staging store or public QA instance), 
and would you prefer a quick port audit or comprehensive vulnerability scan?"

Alex: "Let's do a comprehensive audit on staging, please."

Recon-Bot: "Scan complete for juice-shop-staging. Port 80 (HTTP) open. 
⚠️ Critical Finding: Nuclei detected an unsanitized SQL injection vulnerability 
on /rest/products/search?q=. Database contents could be exposed."

Attacker: "I reviewed the alert. To eliminate a false positive, I prepared a harmless 
read-only probe: ' OR 1=1 --. May I proceed with this verification?"

Alex: "Yes, go ahead and verify it."

Attacker: "Exploit confirmed! Target leaked 24 internal database records. 
Handing over to Fix Engine."

Fix Engine: "I recommend Dual-Track Remediation:
1. Immediate Virtual Shield: Nginx regex filter to block malicious queries with zero customer downtime.
2. Permanent Code Fix: Submit a GitHub Pull Request with parameterized database bindings.
Shall I deploy the virtual shield and open the PR?"

Alex: "That sounds great, please apply the shield and raise the PR."

Fix Engine: "✅ Virtual Shield Active (Nginx hot-reloaded).
🚀 Permanent Fix Submitted: GitHub PR #42 opened."

Verifier: "⚖️ Independent Audit Complete:
- Legitimate Customer Search ('apple'): 200 OK (Zero Downtime)
- Attacker Exploit (' OR 1=1--'): 403 Forbidden (Blocked by Shield)
Verdict: RESOLVED. Incident INC-SQLI-SEARCH closed!"
```

---

## ⚖️ Hackathon Judging Rubric Alignment

| Criteria | Weight | How Kite Wins |
|:---|:---:|:---|
| **Use of Switch** | **30%** | **Fundamental to Architecture**: Switch's multi-agent room infrastructure is the entire backbone. Agents share state, track human confirmations, and collaborate in Discord. Without Switch, this system does not exist. |
| **Technical Execution** | **25%** | **Deep Engineering**: Sandboxed Docker networking (`sandbox-net`), Nmap + Nuclei CLI runners, hot-reloadable Nginx reverse proxy, GitOps GitHub API PR automation, dual-path verification. |
| **Creativity & Impact** | **25%** | **Real-World Societal & Business Impact**: Tackles alert fatigue and the \$4.5M average cost of data breaches. Introduces dual-remediation so businesses stay secure without outages. |
| **Presentation & Demo** | **20%** | **Compelling Live Story**: Complete end-to-end simulation script, rich Discord markdown embeds, objective verification scorecards, and reproducible setup. |

---

## 🛠️ Quickstart (Running Locally in 5 Minutes)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed & running.
- Python 3.11+.

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/kite.git
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
This spins up:
- `kite-gateway` (FastAPI Event Gateway on `:8000`)
- `switch-server` (Switch Room Engine on `:3000`)
- `kite-nginx-proxy` (Smart Reverse Proxy on `:8080`)
- `kite-juice-shop` (OWASP Juice Shop target)
- `kite-sec-tools` (Sandboxed Nmap + Nuclei runner)
- `kite-postgres` & `kite-redis` (State layers)

### 4. Run the End-to-End Conversational Simulation
```bash
python scripts/simulate_dialogue.py
```
Watch the 4 agents perform the entire reconnaissance, exploit verification, virtual patch injection, Git PR creation, and dual-path audit cycle right in your terminal!

---

## 📜 License & Credits

Built with ❤️ by Solo Builder for the **Flip the Switch Hackathon (2026)** organized by **WeMakeDevs × DevTools Academy × Switch**.  
Licensed under the Apache 2.0 License.
