"""Print-friendly stylesheet for report.html."""

CSS = """
:root {
  --ink:#111827; --soft:#475569; --line:#dbe3ec; --paper:#ffffff;
  --blue:#2563eb; --blue-ink:#1e3a8a; --blue-soft:#eff5ff;
  --amber:#d97706; --amber-soft:#fef3c7; --red:#b91c1c; --red-soft:#fee2e2;
}
* { box-sizing:border-box; }
body {
  margin:0 auto; max-width:50rem; padding:2.5rem 1.5rem 4rem;
  font-family:ui-serif, Georgia, "Times New Roman", serif;
  color:var(--ink); background:var(--paper); line-height:1.6; font-size:11.5pt;
}
h1,h2,h3,h4 { font-family:ui-sans-serif, system-ui, -apple-system, sans-serif; line-height:1.25; }
h1 { font-size:2rem; margin:0 0 .35rem; letter-spacing:-.02em; }
h2 {
  font-size:1.25rem; margin:1.5rem 0 .6rem; padding-top:.5rem;
  border-top:2px solid var(--blue); color:var(--blue-ink);
}
h3 { font-size:1.05rem; margin:1.4rem 0 .4rem; }
h4 { font-size:.95rem; margin:1rem 0 .3rem; color:var(--soft); }
p, li { margin:0 0 .58rem; }
a { color:var(--blue-ink); }
code, pre, .mono { font-family:ui-monospace, "SF Mono", Menlo, monospace; font-size:.85em; }

.subtitle { color:var(--soft); font-size:1.02rem; margin-bottom:1rem; }
.byline { color:var(--soft); font-size:.92rem; margin:0 0 1.2rem; }

.linkbar {
  background:var(--blue-soft); border:1.5px solid var(--blue);
  border-radius:10px; padding:.8rem 1rem; margin:1rem 0 1.4rem; font-size:.95rem;
}
.linkbar div { margin:.15rem 0; }
.linkbar .k { display:inline-block; min-width:7.5rem; font-weight:700; color:var(--blue-ink); }

table { width:100%; border-collapse:collapse; margin:.8rem 0 1.1rem; font-size:.88rem;
        font-family:ui-sans-serif, system-ui, sans-serif; }
th, td { border-bottom:1px solid var(--line); padding:.42rem .5rem; text-align:left; vertical-align:top; }
thead th { border-bottom:2px solid var(--blue); color:var(--blue-ink); }
tbody tr:nth-child(even) { background:#f8fafc; }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
tfoot td, tfoot th { border-top:2px solid var(--line); font-weight:700; }

figure { margin:.9rem 0; page-break-inside:avoid; break-inside:avoid; text-align:center; }
/* Cap the height so a tall phone screenshot cannot take a whole page. */
figure img { max-width:100%; max-height:15rem; width:auto; border:1px solid var(--line);
             border-radius:8px; display:inline-block; }
.figrow figure img { max-height:19rem; }
figcaption { font-size:.82rem; color:var(--soft); margin-top:.4rem;
             font-family:ui-sans-serif, system-ui, sans-serif; }

.figrow { display:flex; gap:.9rem; align-items:flex-start; }
.figrow figure { flex:1; margin-top:0; }

pre.evidence {
  background:#0f172a; color:#e2e8f0; padding:.9rem 1rem; border-radius:8px;
  overflow-x:auto; font-size:.76rem; line-height:1.45; white-space:pre-wrap;
  page-break-inside:avoid;
}
pre.evidence .hit { color:#86efac; }

.callout {
  border-left:4px solid var(--blue); background:var(--blue-soft);
  padding:.7rem .95rem; margin:1rem 0; border-radius:0 8px 8px 0; font-size:.93rem;
}
.callout.warn { border-color:var(--amber); background:var(--amber-soft); }
.callout.risk { border-color:var(--red); background:var(--red-soft); }
.callout p:last-child { margin-bottom:0; }

.fill {
  background:#fde68a; border:1px dashed var(--amber); border-radius:4px;
  padding:0 .3rem; font-family:ui-sans-serif, system-ui, sans-serif;
  font-size:.85em; font-weight:700; color:#7a4a00;
}

.kpis { display:flex; gap:.6rem; margin:.8rem 0; page-break-inside:avoid; }
.kpi { flex:1; border:1.5px solid var(--line); border-radius:10px; padding:.7rem .6rem; text-align:center; }
.kpi .v { display:block; font-size:1.25rem; font-weight:800; color:var(--blue-ink);
          font-family:ui-sans-serif, system-ui, sans-serif; }
.kpi .l { font-size:.74rem; color:var(--soft); font-family:ui-sans-serif, system-ui, sans-serif; }

ol.sources { font-size:.84rem; }
ol.sources li { margin-bottom:.35rem; word-break:break-word; }

footer { margin-top:2.5rem; padding-top:1rem; border-top:1px solid var(--line);
         font-size:.82rem; color:var(--soft); }

@media print {
  body { padding:0; font-size:10pt; max-width:none; }
  figure img { max-height:13rem; }
  .figrow figure img { max-height:16rem; }
  h2 { margin-top:1.1rem; }
  h2 { page-break-after:avoid; }
  figure, table, pre.evidence, .callout { page-break-inside:avoid; }
  a { color:var(--ink); text-decoration:none; }
  .linkbar { border-color:var(--line); }
}
@page { margin:16mm 14mm; }
"""
