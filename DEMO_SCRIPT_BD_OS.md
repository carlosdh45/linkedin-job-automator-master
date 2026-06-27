# DobryBot BD OS — 5-Minute Demo Script

**Audience:** Executives, investors, founders, potential clients, BD teams  
**Format:** Screen share, walkthrough of live local instance  
**Goal:** Show how DobryBot turns market noise into qualified, actionable BD opportunities — with human review at every step

---

## Opening Talk Track (30 seconds)

> "Most BD tools either flood you with leads that go nowhere, or they auto-send spray-and-pray emails that burn your reputation. DobryBot is different. It's a local BD operating system that surfaces the right signals, scores them against your ideal customer profile, and prepares deal intelligence — so when you reach out, you already know the company, the pain, and the angle. And nothing ever sends automatically."

---

## Step 1 — Command Center (1 min)

**Navigate to:** `/` (Command Center)

**Talk track:**
> "This is the BD Command Center. Everything you need to run a disciplined deal origination process is here. You can see qualified opportunities ranked by score, high-signal prospects with recommended outreach angles, and companies where we've detected operational pain points."

**Show:**
- Stats row: Qualified Opportunities, High Signal Prospects, BD Drafts, Awaiting Review
- Signal Intelligence panel on the right — highlight that these are **ICP-aware, local, no AI calls**
- Pipeline Snapshot — show deal stages at a glance
- The hero tagline: *"Less noise. More qualified opportunities."*

**Say:**
> "DobryBot doesn't guess. It applies your ICP criteria — your target industries, roles, and pain point priorities — to score every account and surface the ones worth your attention."

---

## Step 2 — Companies + Signals (1 min)

**Navigate to:** `/companies`

**Talk track:**
> "Here are the target accounts scored by ICP fit, pain points, and buying signals. You can see ICP-matched accounts at the top, with hot and warm scores based on detected pain."

**Click:** Filter to "Hot" → show Meridian Labs (score 87) and Vantage Capital (score 80)

**Navigate to:** `/signals`

**Talk track:**
> "Signals are what drive the scoring. Hiring patterns, leadership changes, tech transitions, pain point mentions in job descriptions. Every signal is logged, evaluated, and surfaced here for your review."

**Show:**
- Meridian Labs hiring signal (score 92) — 3 DevOps roles posted
- Vantage Capital leadership change (score 88) — new CTO 6 weeks in
- Click **Evaluate** on one signal → show the recommendation created

**Say:**
> "Evaluating a signal doesn't send anything — it scores the relevance and queues a recommendation for your review."

---

## Step 3 — Opportunities (45 sec)

**Navigate to:** `/opportunities`

**Talk track:**
> "Opportunities are scored combinations of company, contact, pain point, and signal. Each one has a recommended action and a value proposition that reflects the specific pain we've detected."

**Show:**
- Meridian Labs (score 87, Researched) — recommended action: "Reach out via mutual connection"
- Vantage Capital (score 80, Qualified) — new CTO angle
- Click **Recalculate Score** on one — show signal contribution

**Say:**
> "The score isn't a black box. You can see exactly what's driving it — ICP match, pain point count, signal contribution — and recalculate it as new signals come in."

---

## Step 4 — Deal Packets (45 sec)

**Navigate to:** `/deal-packets`

**Talk track:**
> "When an opportunity is qualified, you generate a Deal Packet. Think of it as a full BD briefing — company context, pain points, value proposition, talking points, outreach draft, and a pre-execution checklist. Everything you need before a first outreach."

**Show:**
- Meridian Labs deal packet — In Review status
- Pain points: Manual deployment pipeline, Slow release cycles
- Value proposition: CI/CD automation 60–80% reduction in 6–8 weeks
- Talking points list
- Outreach draft (shows the safety notice at the bottom)
- Checklist progress bar

**Say:**
> "Notice the outreach draft ends with: *Prepared for manual review. DobryBot does not send automatically.* That's a hard rule — it's in the draft itself."

---

## Step 5 — Message Studio (45 sec)

**Navigate to:** `/message-studio`

**Talk track:**
> "Message Studio is where you compose or refine outreach drafts. You provide the context — company, contact, pain point, angle — and DobryBot generates a locally-templated draft. No AI calls, no external APIs."

**Show:**
- Pre-filled context panel: Meridian Labs, Alex Rivera, VP of Engineering
- Select tone: Executive
- Click **Generate Draft** → show the draft preview
- Click **Save Draft for Review** → show success message

**Say:**
> "Saving a draft doesn't send it. It queues it for your review — which is the next step."

---

## Step 6 — Review Queue (45 sec)

**Navigate to:** `/review-queue`

**Talk track:**
> "The Review Queue is where outreach goes to die — or to get approved. Every draft you save arrives here. You review it, check the quality scores, and either approve it, reject it, or flag it for more research."

**Show:**
- BD Outreach tab active — Vantage Capital draft pending
- Tone, angle metadata
- Draft body preview
- Click **Approve Draft (manual execution only)**

**Say:**
> "Approving marks the draft as human-reviewed and ready. It does not send anything. The message stays local. You copy it, paste it, and send it yourself — on your own time, in your own way."

---

## Step 7 — Pipeline (30 sec)

**Navigate to:** `/pipeline`

**Talk track:**
> "Finally, the Pipeline tracks where each deal stands as you advance them through stages — from Identified all the way to Won or Lost. It's a kanban or a list, your choice."

**Show:**
- Kanban view with deal cards across stages
- Meridian Labs in Researched, Vantage Capital in Qualified
- Score badges on each card

**Say:**
> "This isn't just a tracker — every stage transition drives signal evaluation and recommendation generation on the backend. The system learns the shape of your pipeline and surfaces what to do next."

---

## Closing Talk Track (30 sec)

> "What you just saw is a complete BD origination workflow — from signal to scored opportunity to deal packet to human-reviewed outreach. The entire thing runs locally on your machine. No SaaS subscription, no external data calls, no AI providers touching your prospect data. You own the workflow, you own the data, and you make every decision. DobryBot just makes sure you're making the right ones."

---

## Key Demo Phrases

- *"Less noise. More qualified opportunities."*
- *"Prioritize the right prospects with the right context — before outreach."*
- *"Prepared for human review. DobryBot never sends automatically."*
- *"The score isn't a black box — you can see exactly what's driving it."*
- *"Local only. No SaaS. No external APIs. You own everything."*

---

## FAQ / Common Questions

**Q: Is this connected to LinkedIn or email?**  
A: No. DobryBot is fully local. No LinkedIn API, no Gmail, no scraping. All data is entered manually or seeded locally.

**Q: Does it use AI to generate drafts?**  
A: No. Drafts use rule-based local templates — no LLM calls, no API keys required. You can extend this with AI if you want, but the default is fully deterministic.

**Q: Can it auto-apply or auto-send?**  
A: No, by design. Auto-send is explicitly excluded. Every outreach requires human approval and manual execution.

**Q: Who is this for?**  
A: Founders, BD leads, account executives, advisors, and consulting firms who run a disciplined, relationship-driven BD process and want signal intelligence without the noise of traditional CRM tools.

**Q: What makes it different from a CRM?**  
A: Traditional CRMs store contacts and activities. DobryBot *surfaces signal, scores opportunity fit, and prepares deal intelligence* — then tells you exactly what to do and why. It's the intelligence layer before the CRM.
