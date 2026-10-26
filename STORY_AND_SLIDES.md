# ReadyHome — Story, Slide Content & Report Copy

> For Claude Code: use this file as the content source for `slides.html` (reveal.js, ≤10 slides) and for the Motivation and "What is new" sections of `report.html`. Anything in **[FILL: …]** must come from real app runs, tests or user sessions. Never invent those numbers. Keep every source link as written.

---

## The story (narrative spine)

**Origin, in Camille's words (use in the report and on slide 2 speaker notes):**

When I was young, my community lost power for a whole week during Hurricane Sandy. We were lucky: our neighbors helped take care of all of us. My household growing up always had many generations under one roof. My Lola (grandma in Tagalog) lived with us when I was young; later there were young kids, and now there are pets and family members with disabilities and medical needs. Each of them needs something different in an emergency.

A family that is more isolated, or new to the area, or new to the country, may not have neighbors to lean on, especially if cell service goes down. For one adult, evacuating a toddler, a grandparent with a walker and a dog would be a herculean task. That same person could benefit hugely from just **one hour of thinking it through** and **2–3 more hours gathering supplies** (Camille's estimate). But without a baseline, families don't know where to start, and cost keeps many from starting at all.

**Investor lens:** Through the Meng Fund (a student impact investment fund), I scouted early-stage climate adaptation and resilience startups. It's hard to find defensible, differentiated IP in this space. One clear gap stood out: **almost nothing is built for households with mixed evacuation needs.**

**One-line pitch:** ReadyHome is a friendly chat with Sunny that gives mixed households (kids, older adults, people with disabilities, and pets) a readiness score out of 10 and three small, mostly free next steps, each linked to official guidance.

---

## Slide-by-slide content (≤10 slides)

### Slide 1 — Title
- **ReadyHome:** your family's readiness score, one small step at a time
- Camille Bangug · MGT 409 · AI Foundations for Managers
- Sunny (hi pose) + [FILL: live app link] + [FILL: GitHub link]

### Slide 2 — The problem has a face
- Headline: **"One adult. A toddler, a grandparent with a walker, and a dog. The power's out."**
- 3 short lines:
  - Hurricane Sandy: our neighborhood lost power for a week. Neighbors got us through.
  - 71% of people expect help from friends or family after a disaster ([FEMA National Household Survey 2024, copy of FEMA's slides](https://survivingcascadia.com/wp-content/uploads/2025/05/2024-national-household-survey-on-disaster-preparedness-findings.pdf)). What about families who don't have that?
  - Isolated or newly arrived families may have no one to call, and no signal to call with.
- Visual: simple household icons (child, older adult, wheelchair, dog)

### Slide 3 — Why mixed households are hardest
- **71%** of Hurricane Katrina deaths were people over 65 ([CDC, *Preventing Chronic Disease*](https://www.cdc.gov/PCD/ISSUES/2008/jan/07_0135.htm))
- **13 million** US adults aged 50+ say they'd need help to evacuate ([CDC](https://www.cdc.gov/PCD/ISSUES/2008/jan/07_0135.htm))
- **44%** of people who didn't evacuate during Katrina stayed because of their pets ([Australian Journal of Emergency Management](https://knowledge.aidr.org.au/resources/ajem-apr-2015-the-preparedness-and-evacuation-behaviour-of-pet-owners-in-emergencies-and-natural-disasters/))
- **26%** say preparing "costs too much," the #1 barrier ([FEMA NHS 2024](https://survivingcascadia.com/wp-content/uploads/2025/05/2024-national-household-survey-on-disaster-preparedness-findings.pdf))

### Slide 4 — How families solve it today (and the gap)

| Today's option | What it does well | What's missing for mixed households |
|---|---|---|
| [Ready.gov](https://www.ready.gov/kit) | Official kit lists, plan templates | Static and generic. Separate pages per group. |
| [FEMA app](https://www.pcworld.com/article/3537459/5-apps-to-prepare-you-for-any-emergency.html) / [Red Cross Emergency app](https://apps.apple.com/US/app/id954783878) | Alerts, shelter maps | No household profile, no "where do I stand?" |
| [CDC infant checklist](https://www.cdc.gov/nutrition/emergencies-infant-feeding/checklist.html), [AAP Family Readiness Kit](https://www.aap.org/en/patient-care/disasters-and-children/resources-for-families/) | Strong child-specific guidance | PDFs. One need at a time. |
| [Red Cross pre-built kits](https://www.redcross.org/store/4-person-3-day-emergency-preparedness-kit/91053.html) | Convenient | $348 for 4 people. One size fits all. No meds, formula or pets. |
| Registries like [Texas STEAR](https://tdem.texas.gov/response/state-of-texas-emergency-assistance-registry) | Help for people with disabilities | State-by-state, re-enroll yearly, no guaranteed help |
| ChatGPT | Can answer questions | Uncited, no score, no progress tracking, hard to know where to start |

- Takeaway line: **The guidance exists, but it's scattered across 6+ sources and none of them tells a family "here's where you stand, do these 3 things next."**

### Slide 5 — What's new about ReadyHome
1. **One conversation covers the whole household:** kids, older adults, mobility, medical equipment and pets together
2. **A score out of 10** that never marks you down for things that don't apply to you
3. **Just 3 next steps, free ones first,** each showing "+X points" (like insurance discounts for safe habits)
4. **Every tip links to official sources** (Ready.gov, CDC, AAP, Red Cross, ACL, HHS). The app can't invent advice.
5. **Success = steps completed,** not page views

### Slide 6 — How the agents work (diagram)
- Sunny (Survey Bot agent) → score (plain Python) → Coach agent → Verifier → 3 steps
- One line under it: "The AI handles the conversation; plain code does the scoring and checks every link, so the app is cheaper, testable and accurate."
- Model: gpt-6-luna via Portkey (course key)

### Slide 7 — Demo
- Screenshots: landing with Sunny → mid-chat → score reveal (Go-Bag) → 3 step cards → step completed, score goes up
- [FILL: persona used, e.g., "Grandparent on oxygen, no car: 3.5 → 5.0 after 2 steps"]

### Slide 8 — Cost to run
- Per session: [FILL: input / cached / output tokens] = [FILL: $]
- Per user/month: [FILL] · 100 users: [FILL] · 10,000 users: [FILL]
- Cost savers: scoring and step ranking run in plain code (no tokens); quick-reply buttons cut free-text parsing; usage caps on every agent run; daily token budget

### Slide 9 — Safety
- Prompt injection blocked: [FILL: screenshot of the test_injection output]
- Invented steps or links are removed by the verifier
- No medical dosing advice. "Ask your doctor or pharmacist."
- Usage limits stop runaway loops and overspending
- Privacy: ZIP + state only, no street address

### Slide 10 — Impact + what's next
- Impact: [FILL: real tester quote], [FILL: score before → after], [FILL: minutes to finish vs. reading the PDFs], [FILL: steps completed per user]
- The promise: **1 hour of thinking + 2–3 hours of gathering** can turn a herculean evacuation into a manageable one (Camille's estimate)
- Next: full address for county-level hazards and local .gov links; all 50 states; reminders (formula expiry, registry renewal); a shareable plan for caregivers and neighbors; multilingual support for newly arrived families (Tagalog, Spanish and more)

---

## Report copy drafts

### 2. Motivation (draft, ~250 words)
When I was young, my community lost power for a full week during Hurricane Sandy. We got through it because our neighbors helped care for everyone. My household has always had many members with different needs: my Lola lived with us when I was young, and over the years we've had young children, pets, and family members with disabilities and medical needs. In an emergency, each of them needs something different.

Many families don't have a network of neighbors. In FEMA's 2024 National Household Survey, 71% of respondents said they expect help from friends or family after a disaster. Families who are isolated, new to an area, or new to the country may not have that safety net, especially if cell service goes down. The stakes are highest for mixed households. 71% of people who died in Hurricane Katrina were over 65, and 13 million US adults aged 50+ say they would need help evacuating (CDC). After Katrina, 44% of people who didn't evacuate said they stayed because of their pets.

Today, a caregiver has to piece together guidance from Ready.gov, the CDC, the American Academy of Pediatrics, the Red Cross, and state registries. Cost is the #1 barrier people report (26%, FEMA 2024), and pre-built kits are generic and expensive ($348 for a Red Cross 4-person kit). Most importantly, families don't have a baseline, so they don't know where to start. My estimate is that one hour of guided thinking and 2–3 hours of gathering supplies would put most families in a far better position.

### 3. What is new here (draft opener)
I came to this through the Meng Fund, a student impact investment fund, where I scouted early-stage climate adaptation and resilience startups. Defensible, differentiated IP is hard to find in this space, but one gap was consistent: tools treat "a family" as a generic unit, and almost nothing is built for households with **mixed evacuation needs**. ReadyHome combines guidance for children, older adults, people with disabilities and medical equipment, and pets into one conversation and one score. It then breaks that score into three small, mostly free steps, each linked to an official source. [Continue with the comparison table from slide 4.]

---

## Sources
- FEMA 2024 National Household Survey findings (copy of FEMA's slides; the original wasn't located on fema.gov): https://survivingcascadia.com/wp-content/uploads/2025/05/2024-national-household-survey-on-disaster-preparedness-findings.pdf
- CDC, *Preventing Chronic Disease* (2008), older adults and disasters: https://www.cdc.gov/PCD/ISSUES/2008/jan/07_0135.htm
- Australian Journal of Emergency Management (2015), pet owners' evacuation behavior: https://knowledge.aidr.org.au/resources/ajem-apr-2015-the-preparedness-and-evacuation-behaviour-of-pet-owners-in-emergencies-and-natural-disasters/
- Ready.gov Build a Kit: https://www.ready.gov/kit
- CDC infant & young child checklist: https://www.cdc.gov/nutrition/emergencies-infant-feeding/checklist.html
- AAP family resources: https://www.aap.org/en/patient-care/disasters-and-children/resources-for-families/
- Red Cross 4-person kit: https://www.redcross.org/store/4-person-3-day-emergency-preparedness-kit/91053.html
- Red Cross Emergency app: https://apps.apple.com/US/app/id954783878
- FEMA app overview (PCWorld): https://www.pcworld.com/article/3537459/5-apps-to-prepare-you-for-any-emergency.html
- Texas STEAR: https://tdem.texas.gov/response/state-of-texas-emergency-assistance-registry
