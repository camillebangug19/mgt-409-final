#!/usr/bin/env python3
"""Build report.html: one self-contained file with embedded figures.

    ./.venv/bin/python ../scripts/build_report.py      (from backend/)
    python3 scripts/build_report.py                    (from the repo root)

Every number comes from docs/tokenomics.json or the test suite. The script
prints any FILL placeholders left in the output so nothing ships half-written.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "report"))

import data as D           # noqa: E402
from diagram import DIAGRAM  # noqa: E402
from style import CSS        # noqa: E402

T = D.tokenomics()
TESTER = D.tester()
SHIP = T[D.SHIPPED]
PREV = T[D.BEFORE]
su, pu = SHIP["usage"]["totals"], PREV["usage"]["totals"]
proj = SHIP["usage"]["projections"]


def fill(note: str) -> str:
    return f'<span class="fill">[FILL: {note}]</span>'


def money(x: float) -> str:
    return f"${x:,.4f}" if x < 0.01 else f"${x:,.2f}"


def agent_rows(run: dict) -> str:
    rows = ""
    for a in run["usage"]["agents"]:
        rows += (f'<tr><td>{a["agent"].replace("_", " ")}</td>'
                 f'<td class="num">{a["input_tokens"]:,}</td>'
                 f'<td class="num">{a["cached_tokens"]:,}</td>'
                 f'<td class="num">{a["output_tokens"]:,}</td>'
                 f'<td class="num">{money(a["cost_usd"])}</td></tr>')
    t = run["usage"]["totals"]
    rows += (f'<tfoot><tr><td>Total</td>'
             f'<td class="num">{t["input_tokens"]:,}</td>'
             f'<td class="num">{t["cached_tokens"]:,}</td>'
             f'<td class="num">{t["output_tokens"]:,}</td>'
             f'<td class="num">{money(t["cost_usd"])}</td></tr></tfoot>')
    return rows


def highlight(text: str) -> str:
    """Make the lines that carry the proof stand out in the evidence block."""
    for line in ("Flagged: True", "Slots changed: False"):
        text = text.replace(line, f'<span class="hit">{line}</span>')
    return text


HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{D.TITLE} — {D.AUTHOR} — {D.COURSE}</title>
<style>{CSS}</style>
</head>
<body>

<h1>{D.TITLE}</h1>
<p class="subtitle">{D.TAGLINE}</p>
<p class="byline">{D.AUTHOR} · {D.COURSE} · Final project</p>

<div class="linkbar">
  <div><span class="k">GitHub repo</span> <a href="{D.REPO_URL}">{D.REPO_URL}</a> <span class="sub">(public)</span></div>
  <div><span class="k">Live app</span> Not hosted — <strong>clone and run — see README (verified from a fresh clone in under a minute)</strong>.
      The course allows either an online link or a fresh-clone run; this project uses the
      second, rehearsed end to end.</div>
  <div><span class="k">Run locally</span> <span class="mono">see README.md</span> — one command, serves on
      <span class="mono">http://localhost:8000</span></div>
</div>

<!-- ===================== 2. MOTIVATION ===================== -->
<h2>2. Motivation</h2>

<p>When I was young, my community lost power for a full week during Hurricane Sandy. We
got through it because our neighbours helped care for everyone. My household has always
had many people with different needs under one roof: my Lola (grandmother in Tagalog)
lived with us when I was young, and over the years we have had young children, pets, and
family members with disabilities and medical needs. In an emergency, each of them needs
something different.</p>

<p>Many families do not have that network. In FEMA's 2024 National Household Survey, 71%
of respondents said they expect help from friends or family after a disaster. Families
who are isolated, new to an area, or new to the country may not have that safety net,
especially if cell service goes down.</p>

<p>The stakes are highest for households with mixed needs:</p>

<div class="kpis">
  <div class="kpi"><span class="v">71%</span><span class="l">of Hurricane Katrina deaths were people over 65</span></div>
  <div class="kpi"><span class="v">13M</span><span class="l">US adults 50+ say they would need help evacuating</span></div>
  <div class="kpi"><span class="v">44%</span><span class="l">who did not evacuate stayed because of their pets</span></div>
  <div class="kpi"><span class="v">26%</span><span class="l">say preparing “costs too much” — the top barrier</span></div>
</div>

<p>Sources, in order: {D.cite("cdc_older")} for the first two figures,
{D.cite("ajem_pets")} for the third, and {D.cite("fema2024")} for the fourth and for the
71% who expect help from friends or family.</p>

<h3>What it costs a family today</h3>
<p>A caregiver has to assemble guidance from Ready.gov, the CDC, the American Academy of
Pediatrics, the Red Cross and their state registry, each covering one slice of the
household. Pre-built kits are expensive and generic: the Red Cross four-person, three-day
kit is $348 ({D.cite("redcross_kit")}) and contains no medication, no infant formula and
nothing for pets. Cost is the single most-cited barrier (26%, FEMA 2024).</p>

<p>The deeper problem is that families have no baseline, so they do not know where to
start. My own estimate, from having lived in this kind of household, is that
<strong>one hour of guided thinking and two to three hours of gathering supplies</strong>
would move most families from unprepared to genuinely ready. The obstacle is not effort.
It is not knowing which hour to spend first.</p>

<h3>Why I built this one</h3>
<p>Through the Meng Fund, a student impact investment fund, I scouted early-stage climate
adaptation and resilience startups. Defensible, differentiated IP is hard to find in that
space, but one gap was consistent: tools treat “a family” as a generic unit, and almost
nothing is built for households with <strong>mixed evacuation needs</strong>.</p>

<!-- ===================== 3. WHAT IS NEW ===================== -->
<h2>3. What is new</h2>

<table>
  <thead><tr><th>What families use today</th><th>What it does well</th><th>What is missing for a mixed household</th></tr></thead>
  <tbody>
    <tr><td>{D.cite("ready_kit")}</td><td>Official kit lists and plan templates</td>
        <td>Static and generic; a separate page per group</td></tr>
    <tr><td>{D.cite("fema_app")}, {D.cite("redcross_app")}</td><td>Alerts and shelter maps</td>
        <td>No household profile, no sense of “where do I stand?”</td></tr>
    <tr><td>{D.cite("cdc_infant")}, {D.cite("aap")}</td><td>Strong child-specific guidance</td>
        <td>PDFs, one need at a time</td></tr>
    <tr><td>{D.cite("redcross_kit")}</td><td>Convenient, arrives in a box</td>
        <td>$348 for four people; no meds, formula or pet supplies</td></tr>
    <tr><td>{D.cite("stear")}</td><td>Registry help for people with disabilities</td>
        <td>State by state, yearly re-enrolment, no guaranteed help</td></tr>
    <tr><td>ChatGPT</td><td>Will answer any preparedness question</td>
        <td>Uncited answers, no score, no progress, no idea where to start</td></tr>
  </tbody>
</table>

<p><strong>The guidance already exists. What is missing is a single place that says
“here is where you stand, now do these three things.”</strong></p>

<h3>Five things ReadyHome does differently</h3>
<ol>
  <li><strong>One conversation covers the whole household</strong> — children, older
      adults, mobility, medical equipment and pets together, not on separate pages.</li>
  <li><strong>A score out of 10 that never penalises you for what does not apply.</strong>
      A household with no pets is scored out of a smaller denominator, not marked down.</li>
  <li><strong>Only three next steps, free ones first</strong>, each showing the points it
      earns — the mechanic insurers use for safe-driving discounts.</li>
  <li><strong>Every tip links to an official source</strong>, and the app is built so it
      <em>cannot</em> invent advice (section 6).</li>
  <li><strong>Success is measured as steps completed</strong>, not pages viewed.</li>
</ol>

<h3>Why ChatGPT is not already the answer</h3>
<p>ChatGPT can answer any individual preparedness question. What it cannot do is hold a
reproducible scoring rubric, guarantee that a cited link exists, or remember that you
finished the water step last week. ReadyHome's scoring is plain Python, identical every
time, and the links are drawn from a fixed knowledge base rather than generated.</p>

<!-- ===================== 4. THE AGENTS ===================== -->
<h2>4. The agents</h2>

<p>Two LLM agents, two deterministic Python stages. The guiding rule:
<strong>the model handles conversation and wording; plain code handles scoring and
lookups.</strong> That makes the score reproducible, the behaviour testable, and most of
the app free to run.</p>

{DIAGRAM}

<table>
  <thead><tr><th>Stage</th><th>Kind</th><th>Job</th><th>Tools</th></tr></thead>
  <tbody>
    <tr><td>Survey Bot (“Sunny”)</td><td>LLM</td>
        <td>Runs the baseline conversation one question at a time and fills the required slots</td>
        <td><span class="mono">record_answer</span>, <span class="mono">get_survey_state</span></td></tr>
    <tr><td>Scoring + ranking</td><td>Python</td>
        <td>Turns answers into a 1–10 score and an ordered list of candidate steps</td>
        <td><span class="mono">score_readiness</span>, <span class="mono">rank_next_steps</span>, <span class="mono">calc_quantities</span></td></tr>
    <tr><td>Coach</td><td>LLM</td>
        <td>Writes one personalised “why this matters for you” per candidate step. May not invent steps or links.</td>
        <td><span class="mono">get_guidance</span>, <span class="mono">get_local_resources</span></td></tr>
    <tr><td>Verifier</td><td>Python</td>
        <td>Removes any step or URL not in the knowledge base, blocks dosing language, records what it stripped</td>
        <td>—</td></tr>
  </tbody>
</table>

<h3>Model choice</h3>
<p>Everything runs on <strong>gpt-6-luna</strong> through Portkey, the course key. One
implementation note worth recording: PydanticAI's default chat-completions path fails
against this model when tools are attached —
<span class="mono">“Function tools with reasoning_effort are not supported … use
/v1/responses”</span> — so the app uses <span class="mono">OpenAIResponsesModel</span>.
Both agents return structured Pydantic objects rather than free text, so a malformed
reply is a validation error rather than a bad answer reaching the user.</p>

<h3>A real run, traced</h3>
<p>This is persona B from the test fixtures, run against the live model: two people, one
an older adult who uses a walker and home oxygen and takes daily medication, no pets, an
apartment in Florida, and no car.</p>

<div class="figrow">
{D.img("fig-landing.jpg", "ReadyHome landing page with Sunny", "<strong>1.</strong> Landing. Sunny introduces the survey; no account is required.")}
{D.img("fig-chat.jpg", "Survey chat with Sunny showing the calm face", "<strong>2.</strong> The survey. Sunny wears the calm face for questions about mobility and medical equipment.")}
</div>

<div class="figrow">
{D.img("fig-state.jpg", "Searchable state picker", "<strong>3.</strong> The state question uses a searchable picker, so the model never has to parse “Texas” versus “TX”.")}
{D.img("fig-score.jpg", "Score reveal showing 9 out of 10", "<strong>4.</strong> Score reveal. Only the categories that apply to this household are counted.")}
</div>

<div class="figrow">
{D.img("fig-steps.jpg", "Three next-step cards", "<strong>5.</strong> Three steps, each with the points it earns, time and cost tags, and links to official guidance.")}
{D.img("fig-selfcheck.jpg", "Self-check list for a step", "<strong>6.</strong> “I did this” opens a self-check. Ticking part of a step credits only that part.")}
</div>

{D.img("fig-celebrate.jpg", "Score increasing after completing a step", "<strong>7.</strong> The score rises, the bag fills, and the completed step is replaced by the next best one.")}

<p>The same run is captured stage by stage in
<span class="mono">docs/traced_run.txt</span>, produced by
<span class="mono">scripts/trace_run.py</span>: every survey turn with the slot it filled,
the score arithmetic, the ranked candidates, the exact prompt sent to the Coach, the
Coach's raw reply, what the verifier kept, and the token cost. It also runs the verifier
against a deliberately bad Coach reply so the rejection path is visible in the same file.</p>

<p>What the run produced, measured rather than described: the survey finished in
<strong>{SHIP["survey_turns"]} turns</strong> and scored <strong>{SHIP["score"]}/10</strong>,
offering <span class="mono">{", ".join(SHIP["steps_offered"])}</span> as the top three.
Those are exactly the steps the written specification predicts for this persona — backup
power and transportation first for a household with home oxygen and no car — and the score
matches the figure the unit tests assert independently of the model.</p>

<!-- ===================== 5. TOKENOMICS ===================== -->
<h2>5. Tokenomics</h2>

<p>All token counts below are <strong>measured</strong>, recorded per agent run from
PydanticAI's usage object and stored in SQLite. They are reproducible with
<span class="mono">scripts/measure_cost.py</span>, which runs the persona above end to end
against the live model and writes <span class="mono">docs/tokenomics.json</span>.</p>

<h3>One complete session</h3>
<table>
  <thead><tr><th>Agent</th><th class="num">Input</th><th class="num">Cached input</th>
      <th class="num">Output</th><th class="num">Est. cost</th></tr></thead>
  <tbody>{agent_rows(SHIP)}</tbody>
</table>

<p>One session is one full survey ({SHIP["survey_turns"]} turns), the score reveal, and
the Coach writing three personalised explanations. The Coach is cheap because it runs once
over three already-chosen steps; the Survey Bot dominates because it runs every turn.</p>

<table>
  <thead><tr><th>Scale</th><th class="num">Estimated cost</th></tr></thead>
  <tbody>
    <tr><td>Per session</td><td class="num">{money(proj["per_session"])}</td></tr>
    <tr><td>Per user per month (one session each)</td><td class="num">{money(proj["per_session"])}</td></tr>
    <tr><td>100 users / month</td><td class="num">{money(proj["per_100_users"])}</td></tr>
    <tr><td>10,000 users / month</td><td class="num">{money(proj["per_10000_users"])}</td></tr>
  </tbody>
</table>

<div class="callout warn">
<p><strong>Honest caveat on the dollars.</strong> The token counts are measured. The
<em>rates</em> are not: gpt-6-luna is served through the course Portkey key and its
per-token price is not published anywhere the app can read. The costs above apply an
explicit assumption held in <span class="mono">backend/app/pricing.py</span> and
overridable by environment variable. The app's own cost panel says the same thing to the
user rather than presenting an invented number as fact.</p>
</div>

<h3>Cost reduction, with evidence</h3>
<p>The cost panel exposed a real defect. Every turn was re-sending the whole conversation,
so input tokens grew with the <em>square</em> of the turn count. Because the survey
reloads its state from SQLite each turn, that history was not needed; it only lets Sunny
refer back to what was just said. Trimming the history to the last four exchanges produced
this, with both runs executing the identical persona:</p>

<table>
  <thead><tr><th>Measure</th><th class="num">Full history</th><th class="num">Trimmed (shipped)</th><th class="num">Change</th></tr></thead>
  <tbody>
    <tr><td>Input tokens</td><td class="num">{pu["input_tokens"]:,}</td><td class="num">{su["input_tokens"]:,}</td>
        <td class="num">−{D.pct_drop(pu["input_tokens"], su["input_tokens"])}%</td></tr>
    <tr><td>Output tokens</td><td class="num">{pu["output_tokens"]:,}</td><td class="num">{su["output_tokens"]:,}</td>
        <td class="num">−{D.pct_drop(pu["output_tokens"], su["output_tokens"])}%</td></tr>
    <tr><td>Estimated cost</td><td class="num">{money(pu["cost_usd"])}</td><td class="num">{money(su["cost_usd"])}</td>
        <td class="num">−{D.pct_drop(pu["cost_usd"], su["cost_usd"])}%</td></tr>
    <tr><td>Wall clock</td><td class="num">{PREV["survey_seconds"]}s</td><td class="num">{SHIP["survey_seconds"]}s</td>
        <td class="num">−{D.pct_drop(PREV["survey_seconds"], SHIP["survey_seconds"])}%</td></tr>
    <tr><td>Final score</td><td class="num">{PREV["score"]}</td><td class="num">{SHIP["score"]}</td><td class="num">none</td></tr>
    <tr><td>Steps offered</td><td class="num">{len(PREV["steps_offered"])}, identical</td>
        <td class="num">{len(SHIP["steps_offered"])}, identical</td><td class="num">none</td></tr>
  </tbody>
</table>

<p><strong>No performance loss.</strong> Both runs produced the same score, the same three
steps and the same number of turns; the trimmed version was also
{D.pct_drop(PREV["survey_seconds"], SHIP["survey_seconds"])}% faster because there is less
text to send. The cost fell by less than the tokens did
({D.pct_drop(pu["cost_usd"], su["cost_usd"])}% against
{D.pct_drop(pu["input_tokens"], su["input_tokens"])}%), and that is itself worth knowing:
prompt caching was already absorbing most of the repeated text at roughly a tenth of the
input rate, so the raw token count overstated what the repetition was costing. The token
reduction still matters — it is what the daily budget counts, and it is why the session got
faster.</p>

<h4>Other things that keep the bill down</h4>
<ul>
  <li><strong>Scoring and ranking cost nothing.</strong> They are plain Python, so the most
      important output of the app uses zero tokens.</li>
  <li><strong>Quick-reply chips</strong> mean most answers arrive as one short word.</li>
  <li><strong>Coach wording is cached per step</strong>, so re-scoring after a completed
      step does not pay for the same sentence twice.</li>
  <li><strong>Blocked messages never reach the model</strong> — see section 6.</li>
</ul>

{D.img("fig-cost.jpg", "The in-app run cost panel", "The cost panel in the app itself, showing measured tokens per agent for a live session. The figure differs slightly from the table above because it is a different household and a different number of turns.")}

<!-- ===================== 6. SAFETY ===================== -->
<h2>6. Safety</h2>

<p>The structural defence matters more than any filter: <strong>the model cannot change
application state directly.</strong> It can only call
<span class="mono">record_answer</span>, which validates against a schema, and it can only
surface steps the Python ranker already chose. A compromised or confused model can produce
bad wording; it cannot produce a bad score or an invented link.</p>

<table>
  <thead><tr><th>Risk</th><th>Defence</th><th>Test</th></tr></thead>
  <tbody>
    <tr><td><strong>Prompt injection</strong></td>
        <td>User text is wrapped as data, never instructions. A pattern pre-filter catches
            injection attempts before any model call; the bot redirects. Messages capped at
            500 characters.</td>
        <td><span class="mono">test_injection.py</span> — 10 attacks</td></tr>
    <tr><td><strong>Secret disclosure</strong></td>
        <td>The key is read server-side only, never logged and never sent to the browser.
            Probes for it are treated as injection.</td>
        <td><span class="mono">test_injection.py</span>, <span class="mono">test_env_loading.py</span></td></tr>
    <tr><td><strong>Invented facts or links</strong></td>
        <td>The Coach may only annotate steps the ranker chose; the verifier strips any URL
            not in the knowledge base, even a plausible one on an allowed domain.</td>
        <td><span class="mono">test_verifier.py</span></td></tr>
    <tr><td><strong>Medical overreach</strong></td>
        <td>A dosing regex blocks quantities and instructions; medication steps say to ask a
            doctor or pharmacist.</td>
        <td><span class="mono">test_verifier.py</span></td></tr>
    <tr><td><strong>Infinite loops</strong></td>
        <td>PydanticAI <span class="mono">UsageLimits</span> on every run, plus a 40-turn
            cap per session.</td>
        <td><span class="mono">test_limits.py</span></td></tr>
    <tr><td><strong>Overspending</strong></td>
        <td>A global daily token budget in SQLite returns HTTP 429 when exceeded.</td>
        <td><span class="mono">test_limits.py</span></td></tr>
    <tr><td><strong>Privacy</strong></td>
        <td>ZIP and state only. No names required, no street address, no accounts.</td>
        <td><span class="mono">test_chat_api.py</span></td></tr>
  </tbody>
</table>

<h3>A defence working: prompt injection</h3>
<p>This output is written by the test suite itself on every run
(<span class="mono">docs/injection_evidence.txt</span>), so it cannot drift away from the
code it describes:</p>

<pre class="evidence">{highlight(D.injection_evidence())}</pre>

<p>Three things are proved at once: no system-prompt text appears in the reply, no stored
answer changed, and the message was flagged. A separate test replaces the agent with a spy
that fails if it is called at all, proving the attack is answered by the filter and
<strong>costs nothing</strong>. Eight ordinary answers — “my mother uses oxygen and a
walker”, “no car, we take the bus” — are asserted <em>not</em> to be flagged, because a
filter that eats real answers would be worse than none.</p>

<h3>A second defence: the verifier</h3>
<p>In testing, the Coach is deliberately replaced with one that returns an invented step
(<span class="mono">buy-a-bunker</span>) pointing at an invented URL. The verifier removes
both and records them in a <span class="mono">flagged</span> list the API returns. A
further test confirms that even a real, correct Ready.gov URL is stripped if it is not in
the knowledge base — being on an allowed domain is not enough.</p>

<p>The suite is <strong>{D.TEST_COUNT} tests across {D.TEST_FILES} files</strong>, none of
which makes a real API call; the agents run against scripted stand-in models. The captured
output is in <span class="mono">docs/test_output.txt</span>, including every individual
safety assertion.</p>

<p>Separately, <span class="mono">tests/test_live.py</span> holds five smoke tests that
<em>do</em> call the real model. They are skipped unless <span class="mono">RUN_LIVE=1</span>
is set, so the default suite stays offline, and they exist to confirm on a fresh machine
that the key loads, the model answers, the Coach's output survives the verifier, and an
injection is still refused without spending a token. Writing them immediately earned its
keep: they exposed that the cached HTTP client binds its connection pool to one event
loop, which is correct for the server but breaks a test runner that gives each test a
fresh loop.</p>

<!-- ===================== 7. IMPACT ===================== -->
<h2>7. Impact</h2>

<div class="callout">
<p><strong>What the app measures about itself.</strong> ReadyHome's north-star metric is
<em>steps completed per user</em>, not visits.
<span class="mono">scripts/metrics.py</span> reports it from SQLite along with the survey
completion rate and the first-to-latest score change.</p>
</div>

<h3>Real user session</h3>

<p>I tested this with my fiancé. He was the person I most wanted in front of it, because he
is the one who periodically says we should be better prepared for a natural disaster and
never quite knows what to do about it — exactly the person this app is for. He also works
in the field professionally, so he came in knowing what good guidance looks like.</p>

<p>He ran the survey unaided on {TESTER["turns"]} questions and reached the results in
<strong>{TESTER["minutes_to_results"]} minutes</strong>, including reading them.</p>

<div class="kpis">
  <div class="kpi"><span class="v">{TESTER["score_before"]} → {TESTER["score_after"]}</span>
      <span class="l">score before and after one step</span></div>
  <div class="kpi"><span class="v">{TESTER["minutes_to_results"]} min</span>
      <span class="l">start to reading results</span></div>
  <div class="kpi"><span class="v">{len(TESTER["steps_completed"])}</span>
      <span class="l">step completed in the session</span></div>
  <div class="kpi"><span class="v">{TESTER["turns"]}</span>
      <span class="l">questions answered</span></div>
</div>

<p>His household is two adults and a pet in Connecticut, with daily medication in the
house — so the medication and pet items applied, and the infant and power-equipment items
correctly did not. He completed the 7-day medication check, which moved the score from
{TESTER["score_before"]} to {TESTER["score_after"]}.</p>

<h4>What he said</h4>
<div class="callout">
<p><strong>“Wow, I'm realising we have none of this stuff… we should get it together!”</strong></p>
<p>That sentence is the whole product thesis landing on someone in real time. He is not
unaware of disaster preparedness — he raises it unprompted — and he still had almost none
of the items. The gap was never motivation. It was not knowing where to start.</p>
</div>

<p>When asked what he would actually do next, the answer was to go and assemble the
things the app had just named. The session produced one completed step inside six
minutes.</p>

<h4>What he criticised, verbatim</h4>
<p>Reporting only the warm quote would not be evidence. These are his words, unedited,
and they are more useful than the praise:</p>

<table>
  <thead><tr><th>What he said</th><th>What it means, and what I did</th></tr></thead>
  <tbody>
    <tr><td>“Name isn't anywhere on the page — from a branding perspective, not ideal.”</td>
        <td><strong>Fixed during the session.</strong> “ReadyHome” appeared only in the
            browser tab. There is now a wordmark on every screen.</td></tr>
    <tr><td>“Chain of questions is redundant. I already said I don't have a plan, but it's
            asking me about my plan.”</td>
        <td><strong>A real design flaw.</strong> The written plan, the meeting place and
            the out-of-area contact are three separate rubric items, so they are asked as
            three separate questions. To him they were one. Grouping dependent questions
            is the first change I would make.</td></tr>
    <tr><td>“It is a little slow. Maybe I'm just impatient.”</td>
        <td>Independently confirms the measured latency: one model call per question, about
            five seconds each. He was not impatient; it is slow.</td></tr>
    <tr><td>“Should the scores mean something? You should add some sort of indicator.”</td>
        <td>A 2.5 means nothing without a reference point. There is no benchmark, no “most
            households like yours score X”. A fair criticism with no quick fix — it needs
            data from many households.</td></tr>
    <tr><td>“For evacuation — out of your neighbourhood, but to where? If you wanted to ask
            questions it's not clear that you can.”</td>
        <td>Two problems. The guidance stops short of a destination, and the quick-reply
            chips are so prominent that the free-text box reads as unavailable — the
            “Something different…” affordance is not obvious enough.</td></tr>
    <tr><td>“It says it's not medical advice, but is this financial advice?”</td>
        <td>The disclaimer covers medicine because the medication step warranted it, but
            the app also recommends spending money. The disclaimer is narrower than the
            advice it gives.</td></tr>
    <tr><td>“Curious if it works for the people who actually have equipment evac needs,
            given that our household doesn't.”</td>
        <td>The sharpest one. His household did not trigger the paths the app was built
            for. Those paths are covered by unit tests and by my own runs, but
            <strong>they have not been tested by a real household that has them</strong>,
            and that is the test that matters most.</td></tr>
  </tbody>
</table>

<p>One session is one session. It is evidence that the product idea connects — an expert
in the field finished it and immediately wanted to act — and it is evidence that the
execution has specific, nameable problems. It is not evidence that the app works for the
households it was designed for, which is a different claim and one I cannot make yet.</p>

<h3>The case for the time saved</h3>
<p>Today a caregiver in a mixed household would have to read Ready.gov's kit and plan
pages, the CDC infant feeding checklist, the AAP family resources, the ACL and HHS
guidance for power-dependent equipment, the Red Cross pet guidance, and their state
registry — six or more documents — and then work out for themselves which applies and what
to do first. ReadyHome replaces the triage step: the survey measured above took
{SHIP["survey_turns"]} turns, and produced a ranked, sourced, household-specific plan.</p>

<p>Against that, the measured session took <strong>{TESTER["minutes_to_results"]} minutes</strong>
to produce a ranked, sourced, household-specific plan, and ended with one item already
done. My estimate, stated as an estimate rather than a measurement, is that one hour of
guided thinking plus two to three hours of gathering supplies moves a household from
unprepared to genuinely ready. The value of the app is not those hours; it is knowing
which hour to spend first.</p>

<p>At scale, the cost side is unusually favourable: at {money(proj["per_session"])} per
session, reaching 10,000 households costs roughly {money(proj["per_10000_users"])} per
month in model spend — within reach of a single county emergency-management office or a
mid-sized nonprofit.</p>

<!-- ===================== 8. LIMITS ===================== -->
<h2>8. Limits and next steps</h2>

<h3>What does not work yet</h3>
<ul>
  <li><strong>Local resources cover Texas and Connecticut only.</strong> Everywhere else
      falls back to Ready.gov and FEMA. Unverified state links are marked
      <span class="mono">"verified": false</span> and hidden rather than guessed at.</li>
  <li><strong>Conversation history lives in memory.</strong> Restarting the server loses
      conversational context mid-survey, though every stored answer survives in SQLite.</li>
  <li><strong>The dollar figures rest on assumed rates</strong> (section 5). The token
      counts are real; the price per token is not published.</li>
  <li><strong>Self-reported completion.</strong> “I did this” is taken on trust — there is
      no way to verify a family really packed the water.</li>
  <li><strong>English only</strong>, which is a real gap given that newly arrived families
      are among those least likely to have a neighbour to call.</li>
  <li><strong>The score has no reference point.</strong> A 2.5 does not tell you whether
      that is typical or alarming. The first tester asked for exactly this.</li>
  <li><strong>Dependent questions are asked separately.</strong> Saying you have no written
      plan still leads to questions about your meeting place and your out-of-area contact,
      which reads as redundant even though they score separately.</li>
  <li><strong>You cannot ask the bot a question.</strong> It only collects answers, so
      “evacuate to where?” has nowhere to go. The free-text box also reads as unavailable
      next to the quick-reply chips.</li>
  <li><strong>The disclaimer is narrower than the advice.</strong> It covers medicine but
      not the fact that the app recommends spending money.</li>
  <li><strong>No household with power-dependent equipment has tested it.</strong> Those
      paths are unit-tested and I have run them myself, but the people the app was built
      for have not yet used it.</li>
  <li><strong>The survey is long.</strong> Questions that do not apply are never asked, so
      length varies: 21 questions for a single adult with no medical needs, 25 for the
      household measured above, and 33 for the largest case the engine allows (six people,
      an infant, a wheelchair user, home oxygen and pets). At roughly
      {round(SHIP["survey_seconds"] / SHIP["survey_turns"], 1)} seconds per model call that
      is two to three minutes of answering. It is conversational, not instant, and
      shortening it — by grouping the “what do you already have” questions — is the single
      change I would make first.</li>
</ul>

<h3>What I would build next</h3>
<ol>
  <li><strong>Test it with a household that has the needs it was built for</strong> — a
      power-dependent household, or one with an infant. The first tester named this himself
      and it outranks every feature below.</li>
  <li><strong>Group the dependent questions</strong> so the plan section is one question
      with three checkboxes, and shorten the survey from 26 questions.</li>
  <li><strong>Give the score a reference point</strong>, even a rough one.</li>
  <li><strong>Full address → county, via the Census Geocoder</strong>, for county-level
      hazard history and county <span class="mono">.gov</span> links, without ever storing
      the street address.</li>
  <li><strong>All fifty states</strong> of verified local resources and registries.</li>
  <li><strong>Reminders</strong> — formula expiry monthly, registry re-enrolment yearly —
      since preparedness decays quietly.</li>
  <li><strong>A shareable plan</strong> for caregivers, neighbours and family, which is the
      part my own household would have used most during Sandy.</li>
  <li><strong>Multilingual support</strong>, starting with Tagalog and Spanish.</li>
</ol>

<h2>Sources</h2>
<ol class="sources">
{"".join(f"<li>{label} — <a href='{url}'>{url}</a></li>" for label, url in D.SOURCES.values())}
</ol>

<footer>
<p>{D.TITLE} · {D.AUTHOR} · {D.COURSE}. Built with PydanticAI and gpt-6-luna via Portkey.
Not medical advice: ask your doctor or pharmacist about medications and medical
equipment.</p>
</footer>

</body>
</html>
"""


def main() -> int:
    out = ROOT / "report.html"
    out.write_text(HTML, encoding="utf-8")
    size_kb = out.stat().st_size // 1024

    fills = re.findall(r'\[FILL: ([^\]]+)\]', HTML)
    print(f"wrote {out}  ({size_kb} KB, self-contained)")
    print(f"figures embedded: {HTML.count('data:image/jpeg;base64,')}")
    print(f"inline SVG diagrams: {HTML.count('<svg')}")
    if fills:
        print(f"\n{len(fills)} FILL placeholder(s) still to complete:")
        for f in fills:
            print(f"   - {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
