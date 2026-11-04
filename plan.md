# 🪁 KITE — Master Architecture & Build Plan

> **Kite: Autonomous Multi-Agent SecOps Teammate Platform**  
> **Deployment Topology:** On-Host Autonomous SecOps Sidecar on Staging EC2 Instance (`vynn.urbackend.in`) & Local Dev Support.

---

## 🏛️ System Architecture: On-Host EC2 Sidecar Deployment

The platform is deployed directly alongside the application stack on the **Staging AWS EC2 Instance** (or locally via Docker). This grants the agents direct, low-latency access to the local Git repository, local Nginx configurations, and internal socket networking without cloud API rate limits.

```
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                    AWS EC2 INSTANCE (Staging Host / vynn.urbackend.in)           │
 │                                                                                  │
 │  ┌────────────────────────────────────┐   ┌───────────────────────────────────┐  │
 │  │        TARGET APPLICATION          │   │       LOCAL GIT REPOSITORY        │  │
 │  │                                    │   │      /home/ubuntu/target_repo     │  │
 │  │  • Nginx Reverse Proxy (:80/:443)  │   │  (Actual production source code)  │  │
 │  │  • Backend Web Service (Node/Py)   │   │  (Direct git branch, diff, push)  │  │
 │  └─────────────────▲──────────────────┘   └─────────────────▲─────────────────┘  │
 │                    │                                        │                    │
 │        Localhost Network / Sockets              Volume Mount / Read-Write        │
 │                    │                                        │                    │
 │  ┌─────────────────┴────────────────────────────────────────┴─────────────────┐  │
 │  │                  KITE SIDECAR STACK (Docker on EC2)                        │  │
 │  │                                                                            │  │
 │  │  • switch-server & discord-bridge (Outbound WebSocket to Discord Gateway)  │  │
 │  │  • gateway (FastAPI + LangGraph + Pre-Action Action Plan Engine)          │  │
 │  │  • knowledge_base/ (Self-evolving JSON memory: routes, auth, topology)     │  │
 │  │  • sec-tools (Sandboxed Nmap + Nuclei runners)                            │  │
 │  │  • postgres (Persistent incident logs) & redis (Turn context locks)        │  │
 │  └─────────────────────────────────────▲──────────────────────────────────────┘  │
 └────────────────────────────────────────┼─────────────────────────────────────────┘
                                          │
                            Outbound Discord WebSocket
                                          │
                                          ▼
                          ┌───────────────────────────────┐
                          │    ENTERPRISE DISCORD WAR ROOM │
                          │  #general  #recon-feed        │
                          │  #attack-log  #remediation    │
                          │  #verify                      │
                          └───────────────────────────────┘
```

---

## ⚠️ Pre-Action Transparency Protocol (Mandatory Guardrail)

> **Rule:** No agent is permitted to execute active commands, network payloads, Nginx reloads, or code modifications without first presenting a **Pre-Action Execution Manifest** in plain English.

Whenever an agent seeks human approval, it must explicitly outline:
1. **Target**: Exactly which endpoint, file, or service will be touched.
2. **Action Plan**: The exact sequence of commands/payloads it will execute upon confirmation.
3. **Safety Guarantee**: Why this action will not cause data destruction or customer downtime.
4. **Expected Outcome**: What success looks like.

### Example Pre-Action Confirmation Dialogues:

#### 1. Attacker Agent (Before PoC Probe):
> *"🚨 **Attacker Agent — Pre-Action Plan for Approval**  
> If you confirm, here is **exactly what I will execute**:  
> 1. Send a single read-only HTTP GET probe: `/rest/products/search?q=' OR 1=1 --`.  
> 2. Inspect if the database returns hidden records without authentication.  
> 3. **Safety Guarantee:** This is a pure read query; it will not insert, modify, or delete any data.  
> 4. Record evidence and hand off to Fix Engine.  
>   
> **Do you approve this test?**"*

#### 2. Fix Engine Agent (Before Applying Virtual Shield & Git PR):
> *"🛡️ **Fix Engine Agent — Pre-Action Plan for Approval**  
> If you confirm, here is **exactly what I will execute**:  
> 1. **Virtual Shield:** Write `/etc/nginx/conf.d/patch_sqli.conf` with a targeted regex blocking `' OR 1=1` and `UNION SELECT` on `/rest/products/search`.  
> 2. **Zero-Downtime Reload:** Run `nginx -s reload`. (Normal shopper searches like `apple` will experience zero disruption).  
> 3. **Local Git Refactor:** On host `/home/ubuntu/target_repo`, run `git checkout -b secops/fix-sqli`, refactor raw string query into parameterized bindings, and push to GitHub.  
> 4. **Open Pull Request:** Create GitHub PR #42 with detailed diffs.  
>   
> **Should I proceed with deploying the shield and raising the PR?**"*

---

## 🤖 The 4 Specialized Agents & Model Matrix

| Agent | Model | Provider | Primary Role & Guardrails |
|:---|:---|:---|:---|
| **Recon-Bot** | `gemini-3.1-flash-lite` | Google | **Network Profiler & Knowledge Scout**: Ingests Nmap/Nuclei logs. Checks `knowledge_base/` first. If missing, discovers routes and updates memory. |
| **Attacker** | `gpt-6-luna` | OpenAI | **Ethical Pentester**: Validates Recon alerts. Presents Pre-Action Execution Plan before firing safe verification probes. |
| **Fix Engine** | `gpt-6-luna` | OpenAI | **DevSecOps Architect**: Presents Pre-Action Manifest. Deploys Zero-Downtime Nginx hot reload and executes native Git commands on the host repository. |
| **Verifier** | `gemini-3.1-flash-lite` | Google | **Independent Auditor**: Conducts Dual-Path verification (`200 OK` for valid customers vs `403 Forbidden` for exploit attempts). |

---

## 🗂️ Project Directory Structure

```
switch-hack/
├── plan.md                            # This master architecture document
├── docker-compose.yml                 # Multi-container on-host Docker stack
├── .env.example                       # Environment keys template
├── README.md                          # Startup pitch & quickstart guide
│
├── switch/                            # Switch Room Orchestrator
│   ├── config.yaml                    # Switch server configuration
│   └── templates/
│       └── cyberwar-room.template.yaml # Prompts with Pre-Action Transparency rules
│
├── gateway/                           # FastAPI Event Gateway & Core Engine
│   ├── main.py                        # Entrypoint & router mounts
│   ├── config.py                      # Settings & host path bindings
│   ├── knowledge_base/                # Persistent Self-Evolving App Memory
│   │   ├── target_overview.json       # App stack, domain, host mappings
│   │   ├── auth_mechanisms.json       # Login/Register endpoints, token specs
│   │   └── api_inventory.json         # Crawled routes & parameters
│   ├── services/
│   │   ├── knowledge_manager.py       # Read-first caching & completeness calculation
│   │   ├── virtual_patcher.py         # Nginx WAF hot reload manager
│   │   ├── git_service.py             # Local host Git CLI executor (checkout, diff, commit)
│   │   └── github_service.py          # GitHub API integration for remote PRs
│   ├── agents/
│   │   ├── recon_bot.py               # Reconnaissance Agent
│   │   ├── attacker.py                # Attacker Agent (with Pre-Action Plan)
│   │   ├── fix_engine.py              # Fix Engine Agent (with Pre-Action Manifest)
│   │   └── verifier.py                # Verifier Agent (Dual-path regression test)
│   └── routes/
│       └── webhooks.py                # Switch inbound webhook listener
│
├── sandbox/                           # Isolated target environment (for local testing)
│   ├── nginx/
│   │   ├── nginx.conf                 # Reverse proxy configuration
│   │   └── conf.d/                    # Dynamic virtual patch volume
│   └── tools/
│       └── Dockerfile.tools           # Kali-style Nmap & Nuclei container
│
├── scripts/
│   └── simulate_dialogue.py           # 7-turn conversational test runner
│
└── docs/
    ├── FLOWS_AND_TEST_CASES.md        # Plain English test cases with transparency checks
    └── DEMO_SCRIPT.md                 # 2-3 minute timed video demo walkthrough
```

---

## 🐳 Docker Compose Stack (EC2 On-Host Configuration)

```yaml
services:
  # ── Switch Room Orchestration Engine ──
  switch-server:
    image: switchagents/switch:latest
    container_name: switch-server
    ports: ["3000:3000"]
    volumes:
      - ./switch:/app/config
    depends_on: [redis, postgres]
    networks: [secops-net]

  # ── Switch Discord Bridge ──
  discord-bridge:
    image: switchagents/bridge-discord:latest
    container_name: switch-discord-bridge
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - SWITCH_SERVER_URL=http://switch-server:3000
    depends_on: [switch-server]
    networks: [secops-net]

  # ── Core Gateway & Agentic Runtime ──
  gateway:
    build:
      context: ./gateway
      dockerfile: Dockerfile
    container_name: cyberwar-gateway
    ports: ["8000:8000"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_REPO_OWNER=${GITHUB_REPO_OWNER}
      - GITHUB_REPO_NAME=${GITHUB_REPO_NAME}
      - HOST_REPO_PATH=${HOST_REPO_PATH:-/home/ubuntu/target_repo}
      - NGINX_PATCH_DIR=/app/nginx_patches
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://secops:secops_secure_pass@postgres:5432/cyberwar
      - SWITCH_SERVER_URL=http://switch-server:3000
    volumes:
      # Host source code repo mount (for native git commands)
      - ${HOST_REPO_PATH:-./sandbox/target}:/app/target_repo
      # Host/Proxy Nginx virtual patch injection directory
      - ./sandbox/nginx/conf.d:/app/nginx_patches
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on: [switch-server, redis, postgres, nginx-proxy, sec-tools]
    networks:
      - secops-net
      - sandbox-net

  # ── PostgreSQL Persistent State ──
  postgres:
    image: postgres:16-alpine
    container_name: cyberwar-postgres
    ports: ["5432:5432"]
    environment:
      - POSTGRES_USER=secops
      - POSTGRES_PASSWORD=secops_secure_pass
      - POSTGRES_DB=cyberwar
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./gateway/db/migrations/001_initial.sql:/docker-entrypoint-initdb.d/001_initial.sql
    networks: [secops-net]

  # ── Redis Ephemeral State ──
  redis:
    image: redis:7-alpine
    container_name: cyberwar-redis
    ports: ["6379:6379"]
    volumes: [redisdata:/data]
    networks: [secops-net]

  # ── Target App & Smart WAF Reverse Proxy ──
  nginx-proxy:
    image: nginx:alpine
    container_name: cyberwar-nginx-proxy
    ports: ["8080:80"]
    volumes:
      - ./sandbox/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./sandbox/nginx/conf.d:/etc/nginx/conf.d
    depends_on: [juice-shop]
    networks: [sandbox-net]

  juice-shop:
    image: bkimminich/juice-shop:v20.0.0
    container_name: cyberwar-juice-shop
    networks: [sandbox-net]

  sec-tools:
    build:
      context: ./sandbox/tools
      dockerfile: Dockerfile.tools
    container_name: cyberwar-sec-tools
    cap_add: [NET_RAW, NET_ADMIN]
    networks: [sandbox-net]

volumes:
  pgdata:
  redisdata:

networks:
  secops-net:
    driver: bridge
  sandbox-net:
    driver: bridge
```

---

## 🧭 Phased Execution Plan (Checkpoints)

- [x] **Phase 1: Environment & Topology Setup** — Docker Compose stack validated, isolated networks, DB migrations, base Nginx configuration.
- [x] **Phase 2: Gateway & Recon-Bot Agent (`gemini-3.1-flash-lite`)** — Inbound Switch webhook, Nmap/Nuclei scanner runners, conversational clarification handling.
- [x] **Phase 3: Attacker Agent (`gpt-6-luna`) & Safe Exploit Verification** — Pre-Action proposal, non-destructive probe runner, evidence recording.
- [x] **Phase 4: Fix Engine (`gpt-6-luna`) & Dual Remediation** — Pre-Action manifest, Nginx virtual patch hot reload, GitOps Pull Request automation.
- [x] **Phase 5: Verifier Agent (`gemini-3.1-flash-lite`) & Autonomous Loop** — Dual-path regression tests (`200 OK` legitimate traffic vs `403 Forbidden` exploit traffic), Before/After scorecard.
- [x] **Phase 6: Polish, Self-Evolving Knowledge Base & Docs** — Persistent `knowledge_base/` caching, Read-First protocol, README startup pitch, Demo Script.
