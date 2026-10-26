"""The agent architecture diagram, as inline SVG.

Inline rather than an image so it stays crisp when printed and needs no
base64 payload (REQUIREMENTS.md 19.2).
"""

DIAGRAM = '''
<svg viewBox="0 0 790 440" width="100%" role="img"
     aria-label="ReadyHome agent architecture: the chat UI talks to the Survey Bot agent, plain Python scores and ranks, the Coach agent writes the wording, the verifier checks it, and the result returns to the UI."
     font-family="ui-sans-serif, system-ui, sans-serif">
  <defs>
    <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/>
    </marker>
  </defs>
  <style>
    .box   { stroke-width:1.5; rx:10; }
    .llm   { fill:#e8f0fe; stroke:#2563eb; }
    .py    { fill:#fef3c7; stroke:#d97706; }
    .ui    { fill:#ffffff; stroke:#94a3b8; }
    .ttl   { font-size:14px; font-weight:700; fill:#111827; }
    .sub   { font-size:11px; fill:#475569; }
    .lbl   { font-size:11px; fill:#475569; font-style:italic; }
    .key   { font-size:11px; fill:#475569; }
    .flow  { stroke:#475569; stroke-width:1.6; fill:none; marker-end:url(#arw); }
  </style>

  <rect class="box ui" x="20"  y="20"  width="150" height="56"/>
  <text class="ttl" x="95" y="43" text-anchor="middle">Chat UI</text>
  <text class="sub" x="95" y="61" text-anchor="middle">React + Sunny</text>

  <rect class="box llm" x="205" y="14"  width="290" height="68"/>
  <text class="ttl" x="350" y="37" text-anchor="middle">1 · Survey Bot (LLM)</text>
  <text class="sub" x="350" y="55" text-anchor="middle">tools: record_answer,</text>
  <text class="sub" x="350" y="70" text-anchor="middle">get_survey_state</text>

  <rect class="box ui" x="560" y="20"  width="215" height="56"/>
  <text class="ttl" x="667" y="43" text-anchor="middle">SQLite</text>
  <text class="sub" x="667" y="61" text-anchor="middle">answers, events, usage</text>

  <rect class="box py" x="205" y="118" width="290" height="84"/>
  <text class="ttl" x="350" y="140" text-anchor="middle">2 · Plain Python</text>
  <text class="sub" x="350" y="158" text-anchor="middle">score_readiness() → 1–10</text>
  <text class="sub" x="350" y="174" text-anchor="middle">rank_next_steps() → candidates</text>
  <text class="sub" x="350" y="190" text-anchor="middle">calc_quantities()</text>

  <rect class="box llm" x="205" y="238" width="290" height="74"/>
  <text class="ttl" x="350" y="261" text-anchor="middle">3 · Coach (LLM)</text>
  <text class="sub" x="350" y="279" text-anchor="middle">writes “why this matters for you”</text>
  <text class="sub" x="350" y="295" text-anchor="middle">tools: get_guidance,</text>
  <text class="sub" x="350" y="308" text-anchor="middle">get_local_resources</text>

  <rect class="box py" x="205" y="348" width="290" height="70"/>
  <text class="ttl" x="350" y="371" text-anchor="middle">4 · Verifier (Python)</text>
  <text class="sub" x="350" y="389" text-anchor="middle">KB steps and links only,</text>
  <text class="sub" x="350" y="404" text-anchor="middle">no medical dosing</text>

  <rect class="box ui" x="560" y="128" width="215" height="66"/>
  <text class="ttl" x="667" y="151" text-anchor="middle">Knowledge base</text>
  <text class="sub" x="667" y="169" text-anchor="middle">rubric · steps · guidance</text>
  <text class="sub" x="667" y="185" text-anchor="middle">Ready.gov · CDC · Red Cross</text>

  <rect class="box ui" x="20"  y="348" width="150" height="70"/>
  <text class="ttl" x="95" y="374" text-anchor="middle">Score + 3 steps</text>
  <text class="sub" x="95" y="392" text-anchor="middle">“I did this” →</text>
  <text class="sub" x="95" y="408" text-anchor="middle">re-score</text>

  <path class="flow" d="M 170 48 H 200"/>
  <path class="flow" d="M 495 48 H 555"/>
  <path class="flow" d="M 350 82 V 113"/>
  <path class="flow" d="M 350 202 V 233"/>
  <path class="flow" d="M 350 312 V 343"/>
  <path class="flow" d="M 555 160 H 500"/>
  <path class="flow" d="M 205 382 H 175"/>
  <path class="flow" d="M 95 348 V 90"/>

  <text class="lbl" x="360" y="103">profile + answers</text>
  <text class="lbl" x="360" y="224">top candidate steps</text>
  <text class="lbl" x="360" y="334">drafted wording</text>
  <text class="lbl" x="104" y="222">completing a step re-scores</text>

  <rect class="box llm" x="560" y="352" width="22" height="14"/>
  <text class="key" x="590" y="364">LLM does the talking</text>
  <rect class="box py"  x="560" y="378" width="22" height="14"/>
  <text class="key" x="590" y="390">Python does the deciding</text>
</svg>
'''
