# Project Rules: Kite (Autonomous SecOps Teammate)

## Behavioral & Integrity Protocols
- **Absolute Truthfulness:** Always state exactly what has been done and what is pending. Never claim tools, features, or tests are implemented if they haven't been coded and verified.
- **Accurate Status Scorecard:** When presenting status to the user, provide an accurate scorecard separating completed items from pending items without sugarcoating.
- **AI Models:** Exclusively use `gpt-6-luna` (OpenAI with `reasoning_effort="none"`) and `gemini-3.1-flash-lite` (Google GenAI). Never fallback or switch to unapproved models.
- **Action Transparency:** Always explain the planned action and request approval before firing active exploit probes or modifying Nginx/system files.
