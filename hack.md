# ⚡ Flip the Switch Hackathon (2026)

> **Organized by:** WeMakeDevs × DevTools Academy × Switch  
> **Prize Pool:** $10,000+ in cash, hardware & swag  
> **Timeline:** November 4 – 7, 2026 (Ends November 7, 11:59 PM IST)  
> **Format:** 100% Online, Global  
> **Team Size:** Solo or Teams up to 4 members  

---

## 📌 1. Quick Overview & Key Stats

| Metric | Details |
| :--- | :--- |
| **Event Name** | Flip the Switch Hackathon |
| **Duration** | Nov 4 – Nov 7, 2026 (~3 days remaining) |
| **Registration** | 7,195+ Registered Builders |
| **Platform / Venues** | Online (Worldwide) |
| **Official Discord** | [Join WeMakeDevs Discord](https://discord.gg/E2rWw2Yhsm) |
| **Switch Repo** | [GitHub: sandbox-quantum/switch](https://devtoolsacademy.link/wemakedevs) *(Star for Keychron keyboard giveaway)* |
| **Quickstart (10 min)** | [Switch Quickstart Guide](https://docs.switchagents.ai/switch-rooms/getting-started) |
| **Documentation** | [Switch Official Docs](https://docs.switchagents.ai/) |

---

## 🎯 2. The Core Challenge

### **"Turn your solo agent into a teammate"**
Take an AI agent you already use (e.g., Claude Code, Codex, Cursor, OpenCode, Antigravity, LangChain agents, custom agents), connect it via **Switch** to team chat platforms (**Slack, Microsoft Teams, Discord, Telegram, Mattermost**), and build a workflow where humans and agents collaborate to get real tasks done (e.g., triaging, incident response, code review, shipping).

### 🧩 What is Switch?
* **Open Source Infrastructure:** Connects AI agents directly into team chat channels.
* **Rooms:** Every channel becomes a room where agents join with their own name, avatar, memory, and roles.
* **Shared Context:** A shared room log of messages, instructions, roles, tasks, and knowledge accessible to both people and agents.
* **Agent Protocol:** Server-Sent Events (SSE) in, HTTP out. Any agent that speaks HTTP/SSE can join.
* **Switch Console:** A desktop app that runs local agents, manages a local server in Docker, and bridges chat apps.
* *Note:* Switch brings no models/agents itself and doesn't replace chat apps; it acts as the bridge.

---

## 🏆 3. Tracks & Prize Breakdown ($10,000+ Total)

### 🥇 Main Tracks

| Track | Prize | Description & Target |
| :--- | :--- | :--- |
| **Track 01: Best Business Workflow** | **$2,000** Cash | Most practical workflow where people and AI agents get real business/engineering work done. Open to technical and non-technical teams. |
| **Track 02: Best Personal / Creative Workflow** | **$2,000** Cash | Best use of Switch and agents for daily life, personal productivity, creative projects, or unique interactive ideas. |
| **Track 03: Best Core Contribution** | **$2,000** Total<br>($100 × 20 PRs) | Top 20 meaningful pull requests merged/accepted to Switch's open source core repository. |

---

### 🎁 Side Tracks & Giveaways

* 🎙️ **Code with Wispr ($500 Cash):**
  * Best project built using voice dictation via **Wispr Flow** (for prompts, agent instructions, READMEs, etc.).
  * Includes 1 month free of Wispr Flow Pro.
  * Submit Wispr usage scorecard (screenshot from Wispr Flow Desktop Insights).
* 📝 **Best Blog (AirPods 5):**
  * Best technical/walkthrough blog post detailing what you made, architecture, setup, and learnings.
  * Can be entered alongside a project track or standalone.
* ⌨️ **Top 5 Social Posts (#HowISwitch):**
  * Top 5 posts sharing your build on social media with `#HowISwitch` win a **Logitech Mechanical Keyboard**.
* 🎒 **Random Draw Swag:**
  * 20 project submissions selected at random will receive official swag shipped to them.
* 📜 **Participation Certificate:**
  * Every valid project submission receives an official certificate.

---

## 🛠️ 4. Track 03: Core Contribution Rules & Workflow

If you want to contribute directly to the Switch open-source repo for the **$100 / PR** reward:

1. **Browse Issues:** Find open issues on [GitHub tagged `hackathon`](https://github.com/sandbox-quantum/switch/issues?q=is%3Aissue+state%3Aopen+label%3Ahackathon).
2. **Claim & Tag:** Comment on the issue tagging `@petr-sandbox` with a 1-2 sentence solution proposal.
3. **Wait for Assignment:** Do **not** write code until assigned. Only 1 person is assigned per issue.
4. **Dev Setup & CLA:** Read [CONTRIBUTING.md](https://github.com/sandbox-quantum/switch/blob/main/CONTRIBUTING.md) and complete the one-time Contributor License Agreement.
5. **Open PR:** Submit your PR before **November 7, 11:59 PM IST** with `Closes #<issue_number>`.

### ⚠️ Strict Rules for Track 03:
* Max **5 active PRs** open simultaneously per contributor.
* Inactivity for **48 hours** on an assigned issue forfeits your assignment.
* PRs for unassigned issues will **not** be evaluated.
* Low-effort PRs (typo fixes, cosmetic whitespace changes, unreviewed AI slop) will be disqualified.
* No spamming issue assignments.

---

## ⚖️ 5. Judging Criteria

| Weight | Criteria | Description |
| :---: | :--- | :--- |
| **30%** | **Use of Switch** | Is Switch fundamental to the architecture? Would the workflow fail without it? |
| **25%** | **Technical Execution** | Does it work cleanly? Can a judge clone the repo, follow the README, and reproduce it reliably? |
| **25%** | **Creativity & Impact** | Is it a fresh, useful solution solving real bottlenecks faced by teams or individuals? |
| **20%** | **Presentation & Demo** | High quality demo video, clear documentation, and well-explained README illustrating agent interactions. |

### Evaluation Stages:
1. **Initial Review:** Every submission screened by WeMakeDevs.
2. **Shortlist:** Best projects shortlisted by WeMakeDevs.
3. **Finalists:** Judged jointly by core engineers from Switch, DevTools Academy, and WeMakeDevs.

---

## ⚙️ 6. Switch Architecture & Template Reference

Switch uses YAML configuration templates to define agents and rooms.

### Example: Multi-Agent Triage (`triage-pair.template.yaml`)

```yaml
agents:
  - name: "{team}-triager"
    description: Reads incoming reports, files, and routes them
    addressing: anyone
    provider: "{provider}"
    instructions: |
      You are the triager of a small team. For each report:
      1. Restate it in one line.
      2. Decide whether it is a bug, a question, or a request.
      3. Bugs go to the reproducer, by name.

  - name: "{team}-repro"
    description: Reproduces what the triager routes to it
    addressing: owner-agents
    provider: "{provider}"
    instructions: |
      Write the smallest script that shows the problem, run it,
      and report back in the same thread with the exact output.

room:
  name: "{team}-triage"
  bridge: "{bridge}"
  agents: ["{team}-triager", "{team}-repro"]
  users: ["{$creator}"]

kickoff: |
  @{team}-triager and @{team}-repro: this is your triage room.
```

---

## 🚀 7. Step-by-Step Action Plan to Win

1. **Setup:**
   * Install Docker & Switch Console desktop app.
   * Follow the [10-minute Quickstart](https://docs.switchagents.ai/switch-rooms/getting-started).
   * Connect a chat client (Discord server or Slack workspace).
2. **Ideation:**
   * Choose **Track 01 (Business)** (e.g., DevOps incident auto-triage, PR review squad, Customer support escalation) or **Track 02 (Creative/Personal)** (e.g., automated podcast researcher & scriptwriter team, gaming DM assistant, personal finance squad).
   * Or claim an issue under **Track 03 (Core Contribution)** immediately.
3. **Build:**
   * Connect your favorite local CLI/Agent (Claude Code, Cursor, Codex, Antigravity, or custom HTTP agent).
   * Write room prompt & agent coordination rules in template YAML.
4. **Submission Deliverables:**
   * Public GitHub repository with clean code & setup guide.
   * 2-3 minute demo video showing chat interaction.
   * Optional: Wispr Flow scorecard (for extra $500).
   * Optional: Technical blog post (for AirPods 5).
   * Share on X/LinkedIn with `#HowISwitch` (for Logitech keyboard).

---

## 🔗 Useful Links
* [Hackathon Main Page](https://www.wemakedevs.org/hackathons/switch)
* [Resources & Tooling](https://www.wemakedevs.org/hackathons/switch/resources)
* [Switch GitHub Repository](https://github.com/sandbox-quantum/switch)
* [Example Agent Templates](https://github.com/sandbox-quantum/switch/blob/main/examples/agent-templates/triage-pair.template.yaml)
* [WeMakeDevs Community Discord](https://discord.gg/E2rWw2Yhsm)
