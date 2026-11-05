# 🪁 KITE — Master Architecture, Protocol Specification & Build Plan

> **Kite: Autonomous Multi-Agent SecOps Teammate Platform**  
> **Built for:** Flip the Switch Hackathon 2026 (WeMakeDevs × DevTools Academy × Switch)  
> **Track:** Track 01: Best Business Workflow ($2,000 Cash Prize)  
> **Deployment Model:** On-Host Autonomous SecOps Sidecar (AWS EC2 / Staging Host: `vynn.urbackend.in`)

---

## 🏛️ 1. Understanding Switch: The 3 Core Architectural Pillars

According to the official Switch AI architecture (`docs.switchagents.ai`), Switch is built around 3 decoupled components linked over a persistent **PostgreSQL Message Bus**:

```
                              ┌────────────────────────────────────────┐
                              │          EXTERNAL CHAT MESH            │
                              │       (Corporate Discord Server)       │
                              └───────────────────▲────────────────────┘
                                                  │
                                                  ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │ 1. COLLABORATION BRIDGE (Platform Adapter & Room Mapper)                                    │
 │    • Connects to Discord via persistent Outbound WebSocket (`wss://gateway.discord.gg`).   │
 │    • Maps Discord channels into dedicated Switch "Rooms" (e.g., #general ➔ cyberwar-ops).   │
 │    • Streams multi-turn chat history (`room_log`) as shared context for all agents.        │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │ (Shared Message Bus & Event Stream)
                                                ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │ 2. AGENT BRIDGE (Protocol Surface & Multi-Agent Operations Registry)                        │
 │    • Standard Agent Protocol: Server-Sent Events (SSE) Inbound ↓, HTTP Outbound ↑.         │
 │    • Operations Registry: Manages agent sessions (`X-Agent-Id`, `X-Agent-Name`).           │
 │    • Real-Time Watchers: Pushes live room events to connected agent runtimes.              │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
                                                ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │ 3. GATEWAY & OPERATOR CONTROL PLANE (Autonomous Agent Engine)                              │
 │    • Modern OpenAI Function Calling (Tools) & Multi-Model Cognitive Orchestration.          │
 │    • Self-Evolving Persistent Memory (`knowledge_base/` JSON store with completeness %).    │
 │    • Pre-Action Transparency Manifest: Outlines exact payloads before active execution.    │
 │    • Dual-Track Remediation: Zero-Downtime Nginx Virtual Shield + Local Git Pull Request.   │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
                                                ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                             ISOLATED TARGET RUNTIME NETWORK                                 │
 │     AWS EC2 Staging Application (`https://vynn.urbackend.in`) & Local Git Repository        │
 └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 2. Multi-Model Agent Personas & Cognitive Matrix

Kite eliminates hardcoded `if-else` scripts by leveraging modern **OpenAI SDK Native Function Calling (Tools)** combined with **Google Gemini**:

| Agent Persona | Underlying Model | Cognitive Justification & Tool Permissions |
|:---|:---|:---|
| **Kite Lead Orchestrator** | `gpt-6-luna` (or `gpt-4o`) | **General Reasoning & Dialogue Management**: Ingests full room history, speaks natural conversational Hindi/English, and autonomously invokes security tools via function calling. |
| **Recon-Bot** | `gemini-3.1-flash-lite` | **High-Speed Network & Bundle Discovery**: Crawls target JS bundles (`web_discovery.py`), extracts live API routes, and synthesizes Nmap/Nuclei terminal outputs in milliseconds. |
| **Attacker** | `gpt-6-luna` | **Ethical Pentester**: Validates alerts, presents Pre-Action Execution Plans, and fires safe non-destructive read-only probes (`' OR 1=1 --`) to eliminate false positives. |
| **Fix Engine** | `gpt-6-luna` | **DevSecOps Architect**: Formulates Dual-Track Remediation: injects smart Nginx reverse proxy regex filters (`nginx -s reload`) and creates local Git branches (`git checkout -b`). |
| **Verifier** | `gemini-3.1-flash-lite` | **Independent Regression Auditor**: Conducts dual-path testing (verifies legitimate user queries return `200 OK` while exploit payloads return `403 Forbidden`). |

---

## 🛠️ 3. Autonomous Tool Registry (Native OpenAI Function Calling)

Instead of regex intent matching, the model autonomously chooses and executes these Python tools:

```python
tools = [
    {
        "name": "discover_target_endpoints",
        "description": "Crawls target web bundles (JS), inspects HTTP headers, and extracts live API routes and auth endpoints.",
        "parameters": {"target_url": "string"}
    },
    {
        "name": "read_knowledge_base",
        "description": "Reads persistent knowledge files (target_overview, auth_mechanisms, api_inventory) to check existing memory.",
        "parameters": {"category": "target_overview | auth_mechanisms | api_inventory"}
    },
    {
        "name": "run_security_scan",
        "description": "Executes sandboxed Nmap port detection and Nuclei template scans against an asset.",
        "parameters": {"target": "string"}
    },
    {
        "name": "verify_safe_exploit_probe",
        "description": "Fires a non-destructive read-only PoC probe to confirm vulnerability without data alteration.",
        "parameters": {"endpoint": "string", "payload": "string"}
    },
    {
        "name": "apply_virtual_shield",
        "description": "Injects a targeted regex filter into Nginx reverse proxy and triggers a zero-downtime hot reload.",
        "parameters": {"endpoint": "string"}
    }
]
```

---

## 🧠 4. Self-Evolving Persistent Knowledge Base (`knowledge_base/`)

Knowledge starts **100% CLEAN (0% completeness)** on fresh deployments. As agents interact with targets, they update structured JSON caches with concrete completeness heuristics:

```
gateway/knowledge_base/
├── target_overview.json     # App domain, business logic, base URL (starts at 0%)
├── auth_mechanisms.json     # Discovered login/register routes, payload schemas, JWT specs
└── api_inventory.json       # All crawled REST/API routes extracted from live bundles
```

### Read-First Protocol:
1. Agent checks `read_knowledge_base(category)`.
2. **If completeness $\ge 70\%$** ➔ Instant cache hit (0 latency, 0 token waste).
3. **If completeness $< 70\%$ or empty** ➔ Triggers `discover_target_endpoints()` to spider the real app and populates the cache dynamically.

---

## 🛡️ 5. Key Innovation: Dual-Track Remediation

When a critical vulnerability is confirmed, Kite enforces **zero customer downtime**:

```
                       [FIX ENGINE (`gpt-6-luna`)]
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
 [Layer 1: Immediate Shield]                    [Layer 2: Permanent Fix]
  (Zero-Downtime Virtual Patch)                  (GitOps Pull Request)
         │                                                   │
 • Injects targeted regex into Nginx            • Native Git on host (`/home/ubuntu/vynn`):
   (`/etc/nginx/conf.d/patch_sqli.conf`).         `git checkout -b secops/fix-sqli-patch`
 • Runs `nginx -s reload` in 5ms.               • Refactors raw SQL queries into safe
 • Malicious strings (`' OR 1=1`) ➔ 403.          parameterized prepared statements.
 • Genuine customer queries ➔ 200 OK!           • Opens GitHub Pull Request with code diffs.
```

---

## ⚠️ 6. Pre-Action Transparency Protocol

No agent executes active probes, Nginx modifications, or Git commits without first delivering a **Pre-Action Execution Manifest**:

1. **Target:** Specific URL, endpoint, or file.
2. **Action Plan:** Concrete sequence of commands/requests to be fired.
3. **Safety Guarantee:** Why this action will not cause data destruction or customer downtime.
4. **Expected Outcome:** Clear success/failure criteria.

---

## 🧭 7. Phased Execution Roadmap

- [x] **Phase 1: Environment & Topology Setup** — Docker Compose stack running, Postgres & Redis state stores, isolated networking.
- [x] **Phase 2: Switch Collaboration Bridge & Room Context** — Persistent Discord WebSocket gateway connected, multi-turn `room_log` history streaming.
- [x] **Phase 3: Agentic Engine & Native Tool Calling** — Rebuilt `agent_engine.py` using OpenAI Function Calling (replaces hardcoded `if-else`).
- [x] **Phase 4: Real Web Discovery Engine** — Implemented `web_discovery.py` (JS bundle crawler, Swagger detector).
- [x] **Phase 5: Self-Evolving Knowledge Base** — Reset knowledge base to 0% initial state for dynamic target learning.
- [x] **Phase 6: Dual-Remediation & Host Git Operations** — Nginx hot-reloader and native Git CLI manager (`git_service.py`).
