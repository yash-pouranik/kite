# 📑 CyberWar-Room: Flows, Conversational Protocols & Plain-English Test Cases

> **Standard Operating Procedures (SOP) & Behavioral Scenarios for Autonomous Multi-Agent SecOps**

---

## 💬 Natural Language Conversational Protocol

In the CyberWar-Room, human engineers interact naturally like colleagues in a corporate Slack/Discord channel. There are **no rigid CLI commands or robotic syntax** like `@recon-bot scan target:juice-shop` or `APPROVE FIX-01`.

### Key Human-Agent Interaction Principles:
1. **Natural Dialogue Understanding**: Agents parse normal conversational sentences (e.g., *"Hey team, could someone run a check on our staging store before we release today?"*).
2. **Autonomous Clarification Questions**: If a human command is ambiguous or missing context, the agent does not fail or guess wildly—it politely asks an open clarifying question before taking action.
3. **Plain English Risk Communication**: Technical findings (CVEs, CVSS scores) are translated into clear business impact (e.g., *"An attacker could read confidential customer addresses without logging in"*).
4. **Natural Approval & Feedback**: Humans approve or reject suggestions naturally (e.g., *"Go ahead and apply the block"*, *"Wait, don't do that because our QA team is running tests"*, or *"Can we restrict it to our VPN instead?"*).

---

## 🛡️ Dual-Track Remediation Architecture

When a vulnerability is discovered, the **Fix Engine** (`gpt-6-luna`) does not take down the entire API or blindly rewrite production files on a running container. Instead, it deploys a **two-tier defense**:

```
                       [FIX ENGINE (`gpt-6-luna`)]
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
 [Layer 1: Immediate Shield]                    [Layer 2: Permanent Fix]
  (Zero-Downtime Virtual Patch)                  (GitOps Pull Request)
         │                                                   │
 • Injects a targeted Nginx reverse-            • Automatically branches repo:
   proxy regex rule (hot reload).                 `fix/sqli-search-endpoint`.
 • Only blocks malicious attack strings         • Refactors vulnerable code using
   (e.g., `' OR 1=1`, `UNION SELECT`).            safe parameterized queries.
 • Legitimate customer searches                 • Submits GitHub Pull Request with
   (`apple`, `shirts`) remain 100% functional.    detailed vulnerability explanation.
 • Prevents outages and downtime.               • Ready for standard team review.
```

---

## 🔀 System Behavioral Flows

```
Flow 1: Standard Conversational Path (Ambiguity ➔ Clarification ➔ Discovery ➔ Exploit ➔ Virtual Patch + Git PR ➔ Dual Verification)
Flow 2: Human Override & Collaborative Redirection (Human Guidance & Context Sharing)
Flow 3: Self-Healing Remediation Loop (Virtual Patch Bypass Detected ➔ Automatic Policy Hardening)
Flow 4: Clean Bill of Health (No Action Required)
```

---

## 📖 Plain English End-to-End Test Cases

### 🟢 Test Case 1: Full Conversational Lifecycle (Clarification, Discovery, Virtual Patch & Git PR)

* **Initial Environment:**
  - OWASP Juice Shop running behind an Nginx reverse proxy.
  - Switch Core connected to Discord channels (`#incidents`, `#recon-feed`, `#attack-log`, `#remediation`, `#verify`).
  - All 4 agents online with shared conversational memory.

* **Turn 1: Natural Human Prompt (Intentionally Ambiguous)**
  - **Human (Alex, SecOps Lead):** 
    > *"Morning team! Could someone scan our store environment? Want to make sure we're clean before the marketing campaign."*

* **Turn 2: Agent Seeks Clarification**
  - **Recon-Bot (`gemini-3.1-flash-lite`):**
    > *"Good morning Alex! I see two store configurations: our internal staging environment (`juice-shop-staging`) and the public QA instance. Which one would you like me to profile, and should I run a quick discovery or a comprehensive vulnerability scan?"*

* **Turn 3: Human Clarification**
  - **Human:**
    > *"Let's do a comprehensive scan on staging, please."*

* **Turn 4: Reconnaissance Execution & Reporting**
  - Recon-Bot runs sandboxed Nmap and Nuclei against the staging container.
  - Recon-Bot posts in `#recon-feed`:
    > *"Scan complete for `juice-shop-staging`. We have Port 80 (HTTP) open through our Nginx reverse proxy. 
    > ⚠️ **Critical Finding**: Nuclei detected an unsanitized SQL injection vulnerability on the product search endpoint (`/rest/products/search?q=`). An attacker could manipulate this parameter to query backend database tables directly."*

* **Turn 5: Attacker Proposes Non-Destructive Exploit Probe**
  - **Attacker Agent (`gpt-6-luna`):**
    > *"I noticed the SQL injection alert from Recon-Bot. To eliminate a potential false positive and verify if this can actually be exploited, I've prepared a harmless read-only test probe: `' OR 1=1 --`. 
    > This will only test if hidden catalog records are exposed. May I proceed with this verification probe?"*

* **Turn 6: Human Approval**
  - **Human:**
    > *"Yes, go ahead and verify it."*

* **Turn 7: Exploit Execution & Proof Delivery**
  - Attacker Agent dispatches the probe and records the HTTP response.
  - Attacker Agent posts in `#attack-log`:
    > *"Exploit confirmed. The search endpoint returned 24 hidden records, including test products and internal database entries without any authentication. 
    > Proof of exploit attached. The vulnerability is verified active. Handing over to Fix Engine."*

* **Turn 8: Fix Engine Recommends Dual-Track Remediation**
  - **Fix Engine (`gpt-6-luna`):**
    > *"I've formulated a dual remediation plan so we don't disrupt active shoppers:
    > 1. **Immediate Virtual Patch**: I'll inject an inspection rule into Nginx that blocks SQL injection patterns (`UNION SELECT`, quote escaping, `--`) on `/rest/products/search`. Legitimate shopper searches like `juice` or `mug` will continue working normally with zero downtime.
    > 2. **Permanent Code Fix**: I'll create a branch in our GitHub repository (`fix/sqli-search-parameterized`) and open a Pull Request refactoring the raw query into a parameterized prepared statement.
    > 
    > Shall I deploy the virtual shield and open the PR?"*

* **Turn 9: Human Approves Fix**
  - **Human:**
    > *"That sounds solid. Please apply the virtual shield and submit the PR."*

* **Turn 10: Execution of Shield & Pull Request**
  - Fix Engine injects `virtual_patch_sqli.conf` into Nginx and runs `nginx -s reload` (hot reload).
  - Fix Engine connects to GitHub, branches the repository, refactors the query, and opens PR #14.
  - Fix Engine posts in `#remediation`:
    > *"✅ Immediate Shield Active: Nginx hot-reloaded with targeted query filter.
    > 🚀 Permanent Code Fix Submitted: [GitHub PR #14: Refactor search queries to parameterized bindings](https://github.com/company/store/pull/14).
    > Requesting Verifier Agent to audit both legitimate traffic and attack vectors."*

* **Turn 11: Verifier Dual-Path Audit**
  - **Verifier Agent (`gemini-3.1-flash-lite`)** performs two real-world tests:
    1. **Customer Search Test:** Sends `GET /rest/products/search?q=apple` ➔ Response: **`200 OK`** (Valid products returned).
    2. **Attack Exploit Test:** Sends `GET /rest/products/search?q=apple' OR 1=1--` ➔ Response: **`403 Forbidden`** (Attack blocked by virtual patch).
  - Verifier Agent posts in `#verify`:
    > *"🛡️ Audit Results:
    > - **Legitimate User Traffic (`q=apple`)**: Working normally (Status: 200 OK). No service disruption.
    > - **Attacker Payload (`' OR 1=1--`)**: Successfully blocked (Status: 403 Forbidden).
    > - **Verification Verdict**: ✅ RESOLVED. Incident closed."*

---

### 🟡 Test Case 2: Human Collaborative Redirection (Context Sharing & Scope Adjustment)

* **Initial Situation:**
  - Recon-Bot notices Port 22 (SSH) open on an auxiliary container and suggests immediately dropping it.
* **Turn 1: Fix Engine Proposes Disruptive Action**
  - **Fix Engine:**
    > *"Port 22 (SSH) is publicly accessible on our staging container, exposing it to potential brute-force attempts. Should I block port 22 completely via iptables?"*
* **Turn 2: Human Provides Business Context (No Rigid Commands)**
  - **Human:**
    > *"Wait, don't close port 22 right now. Sarah from the infrastructure team needs SSH access to debug deployment scripts today."*
* **Turn 3: Agent Adapts & Proposes Safe Alternative**
  - **Fix Engine:**
    > *"Understood, Alex. I will not close Port 22. 
    > As a safer compromise, would you like me to restrict SSH access so only Sarah's static office VPN subnet (`10.24.0.0/16`) can connect, while dropping all public internet attempts? That way Sarah won't be interrupted, but external attackers are locked out."*
* **Turn 4: Human Agrees to Safer Proposal**
  - **Human:**
    > *"Yes, that's much better. Restrict it to the VPN subnet."*
* **Turn 5: Outcome:**
  - Fix Engine applies the refined subnet rule. The system demonstrates conversational adaptability and respects business context without breaking developer workflows.

---

### 🔴 Test Case 3: Fix Bypass & Self-Healing Loop

* **Turn 1:** Fix Engine applies an initial regex virtual patch against standard SQL injection keywords.
* **Turn 2:** Verifier Agent tests the patch using standard payload: Blocked (`403 Forbidden`).
* **Turn 3:** Verifier Agent tests with an advanced evasion technique (hex-encoded / URL-encoded payload: `%27%20UNION%20SELECT`).
* **Turn 4: Bypass Detected**
  - The unhardened regex fails to decode before matching, allowing data leakage.
  - **Verifier Agent:**
    > *"⚠️ Alert: The initial virtual patch was bypassed using URL-encoded payloads (`%27%20UNION`). The backend still returned unauthorized database rows. Handing back to Fix Engine for policy hardening."*
* **Turn 5: Fix Engine Upgrades Filter**
  - Fix Engine analyzes the bypass and upgrades the Nginx configuration to include URL normalization and multi-pass decoding.
* **Turn 6: Re-Verification & Resolution**
  - Verifier Agent re-tests: Both raw and encoded payloads now return `403 Forbidden`.
  - Verifier Agent posts: *"Hardened patch verified effective against encoding evasions. System secure."*

---

### ⚪ Test Case 4: Clean Scan (Baseline Security Maintained)

* **Turn 1: Human Request**
  - **Human:**
    > *"Hey team, did the overnight scan on our payment gateway find anything?"*
* **Turn 2: Recon-Bot Status Report**
  - **Recon-Bot:**
    > *"Good morning! The automated audit of our payment gateway completed at 03:00 UTC. 
    > - Open ports: Only Port 443 (HTTPS) active.
    > - Nuclei vulnerability checks: 0 vulnerabilities or misconfigurations detected.
    > - TLS configuration: Grade A+ (TLS 1.3 enforced).
    > Security posture is 🟢 OPTIMAL. Attacker and Fix Engine remain standing by."*
* **Turn 3: Result:**
  - Pipeline exits cleanly. No unnecessary alarms, approval requests, or pipeline bloat.
