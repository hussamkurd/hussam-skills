#!/usr/bin/env python3
"""Render a senior-review review.md as one self-contained review.html.

Usage:
    python3 render_html.py <review.md or review folder> [-o <out.html>]

Reads only the review.md the skill already wrote, so it can run any time
after a review (before or after the decisions) without re-running the
lanes. Python 3.8+, standard library only. The page has inline CSS and a
few lines of inline JS for the filters; it needs no network.
"""
import argparse
import html
import re
import sys
from pathlib import Path

SEVERITIES = ("critical", "code", "trivial")
FIELD_ORDER = ("Where", "Today", "Change", "Why", "Evidence", "Check",
               "If skipped", "Recommendation", "Decision")


# ---------- parsing ----------

def split_sections(text, level):
    """Split text on headings of exactly `level` hashes -> [(title, body)]."""
    pattern = re.compile(r"^%s (.*)$" % ("#" * level), re.M)
    parts, last, title = [], 0, None
    for m in pattern.finditer(text):
        if title is not None or m.start() > 0:
            parts.append((title, text[last:m.start()]))
        title, last = m.group(1).strip(), m.end()
    parts.append((title, text[last:]))
    return parts


def find_section(sections, *names):
    for title, body in sections:
        if title and any(title.lower().startswith(n.lower()) for n in names):
            return body
    return ""


def parse_table(body):
    rows = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 2:
        return [], []

    def cells(row):
        row = row.strip().strip("|")
        return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]

    header = cells(rows[0])
    data = [cells(r) for r in rows[2:] if not re.fullmatch(r"[|\s:-]+", r)]
    return header, data


def header_value(text, key):
    m = re.search(r"^%s:\s*(.+)$" % re.escape(key), text, re.M)
    return m.group(1).strip() if m else ""


def parse_fields(body):
    """Read '- Key: value' bullets; continuation lines and fences join the value."""
    fields, key, buf, in_fence = {}, None, [], False
    known = "|".join(re.escape(k) for k in FIELD_ORDER)
    start = re.compile(r"^- (%s):\s?(.*)$" % known)
    for line in body.splitlines():
        stripped = line.strip()
        m = None if in_fence else start.match(line)
        if m:
            if key:
                fields[key] = "\n".join(buf).strip()
            key, buf = m.group(1), [m.group(2)]
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
        if key is not None:
            buf.append(line[2:] if line.startswith("  ") else line)
    if key:
        fields[key] = "\n".join(buf).strip()
    return fields


def parse_findings(text):
    findings = []
    for sev_title, sev_body in split_sections(text, 3):
        if not sev_title:
            continue
        sev = next((s for s in SEVERITIES if s in sev_title.lower()), None)
        if not sev:
            continue
        for title, body in split_sections(sev_body, 4):
            if not title:
                continue
            m = re.match(r"#?(\d+)\s+(.*)", title)
            num, name = (m.group(1), m.group(2)) if m else ("", title)
            findings.append({"num": num, "title": name, "severity": sev,
                             "fields": parse_fields(body)})
    return findings


def parse(md):
    top = split_sections(md, 2)
    preamble = top[0][1] if top and top[0][0] is None else ""
    title_m = re.search(r"^#\s+(.*)$", md, re.M)
    summary = find_section(top, "Summary")
    summary_text = "\n".join(
        ln for ln in summary.splitlines()
        if ln.strip() and not re.match(r"^(Verdict|Confidence|Decision|Codex gate):", ln.strip()))
    coverage = []
    cov_body = find_section(top, "Requirement coverage")
    for ln in cov_body.splitlines():
        m = re.match(r"^-\s*(covered|gap|partial)\s*:\s*(.*)$", ln.strip(), re.I)
        if m:
            coverage.append((m.group(1).lower(), m.group(2)))
    cov_note = "" if coverage else cov_body.strip()
    verify_body = find_section(top, "Verification")
    staging = ""
    sm = re.search(r"Staging checks before production:(.*)", verify_body, re.S)
    if sm:
        staging = sm.group(1).strip()
    return {
        "title": (title_m.group(1) if title_m else "Senior Review").replace("Senior Review:", "").strip(),
        "base": header_value(preamble, "Base"),
        "principles": header_value(preamble, "Project principles"),
        "uncommitted": header_value(preamble, "uncommitted files not reviewed"),
        "summary": summary_text,
        "verdict": header_value(summary, "Verdict"),
        "confidence": header_value(summary, "Confidence"),
        "decision": header_value(summary, "Decision"),
        "codex": header_value(summary, "Codex gate"),
        "components": parse_table(find_section(top, "Components")),
        "safety": parse_table(find_section(top, "Safety answers")),
        "coverage": coverage,
        "coverage_note": cov_note,
        "verification": parse_table(verify_body),
        "staging": staging,
        "previous": parse_table(find_section(top, "Previous spec")),
        "findings": parse_findings(find_section(top, "Findings")),
    }


# ---------- inline rendering ----------

def inline(text):
    """Escape, then render `code`, **bold** and #n finding links."""
    out, pos = [], 0
    for m in re.finditer(r"`([^`]+)`", text):
        out.append(_plain(text[pos:m.start()]))
        out.append("<code>%s</code>" % html.escape(m.group(1)))
        pos = m.end()
    out.append(_plain(text[pos:]))
    return "".join(out)


def _plain(text):
    s = html.escape(text)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w&])#(\d+)\b", r'<a class="ref" href="#f\1">#\1</a>', s)
    return s


def block(text):
    """Paragraphs, bullet and numbered lists, and fenced code (diff aware)."""
    parts, para, items, fence, lang = [], [], [], None, ""

    def flush():
        if para:
            parts.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()
        if items:
            parts.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(i) for i in items))
            items.clear()

    for line in text.splitlines():
        s = line.strip()
        if fence is not None:
            if s.startswith("```"):
                parts.append(code_block(fence, lang))
                fence = None
            else:
                fence.append(line)
            continue
        if s.startswith("```"):
            flush()
            fence, lang = [], s[3:].strip()
        elif not s:
            flush()
        elif re.match(r"^([-*]|\d+\.)\s+", s):
            if para:
                flush()
            items.append(re.sub(r"^([-*]|\d+\.)\s+", "", s))
        elif items:
            items[-1] += " " + s
        else:
            para.append(s)
    if fence is not None:
        parts.append(code_block(fence, lang))
    flush()
    return "".join(parts)


def code_block(lines, lang):
    indent = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    lines = [l[indent:] for l in lines]
    is_diff = lang == "diff" or any(l.startswith(("+ ", "- ", "+\t", "-\t")) for l in lines)
    rows = []
    for l in lines:
        cls = ""
        if is_diff and l.startswith("+"):
            cls = "add"
        elif is_diff and l.startswith("-"):
            cls = "del"
        rows.append('<span class="ln %s">%s</span>' % (cls, html.escape(l) or " "))
    return '<pre class="code">%s</pre>' % "".join(rows)


# ---------- classification ----------

def verdict_tone(v):
    v = v.lower()
    if "do not" in v:
        return "bad"
    if "after" in v:
        return "warn"
    return "good" if v.startswith("ship") else "muted"


def first_word(v):
    m = re.match(r"\W*(\w+)", v or "")
    return m.group(1).lower() if m else ""


def rec_of(f):
    return first_word(f["fields"].get("Recommendation", ""))


def decision_of(f):
    d = f["fields"].get("Decision", "").strip()
    w = first_word(d)
    return w if w in ("accept", "accepted", "reject", "rejected", "defer", "deferred") else ""


def norm(word):
    return {"accepted": "accept", "rejected": "reject", "deferred": "defer"}.get(word, word)


def result_tone(r):
    r = r.lower()
    if r.startswith(("pass", "killed", "fixed", "covered")):
        return "good"
    if r.startswith(("fail", "survived", "still")):
        return "bad"
    return "warn"


def worst_sev(cell):
    low = cell.lower()
    return next((s for s in SEVERITIES if s in low), "none")


# ---------- page ----------

def chip(text, tone):
    return '<span class="chip %s">%s</span>' % (tone, inline(text))


def render(r):
    fs = r["findings"]
    counts = {s: sum(1 for f in fs if f["severity"] == s) for s in SEVERITIES}
    recs = {k: sum(1 for f in fs if rec_of(f) == k) for k in ("accept", "reject", "defer")}
    decided = sum(1 for f in fs if decision_of(f))
    body = [
        hero(r, counts, recs, decided, len(fs)),
        section("What changed", components(r) + safety(r), "changed"),
        section("Findings", findings(fs), "findings") if fs else
        section("Findings", '<p class="empty">No findings. A clean change.</p>', "findings"),
        section("Requirement coverage", coverage(r), "coverage"),
        section("Verification", verification(r), "verification"),
    ]
    if r["previous"][1]:
        body.insert(2, section("Previous spec", simple_table(r["previous"], 1), "previous"))
    return PAGE.format(title=html.escape(r["title"] or "Senior Review"),
                       css=CSS, js=JS, body="".join(body))


def section(title, content, anchor):
    return '<section id="%s"><h2>%s</h2>%s</section>' % (anchor, html.escape(title), content)


def hero(r, counts, recs, decided, total):
    v = r["verdict"] or "No verdict"
    conf = r["confidence"]
    level = first_word(conf)
    conf_head, _, conf_rest = conf.partition(".")
    bars = {"high": 3, "medium": 2, "low": 1}.get(level, 0)
    meter = "".join('<i class="%s"></i>' % ("on " + level if i < bars else "") for i in range(3))
    stats = "".join(
        '<a class="stat %s" href="#findings" data-filter="%s"><b>%d</b><span>%s</span></a>'
        % (s, s, counts[s], s) for s in SEVERITIES)
    rec_line = " · ".join("%d %s" % (recs[k], k) for k in recs if recs[k])
    decision = r["decision"]
    pending = not decision or "pending" in decision.lower()
    dec_html = (chip("Decisions pending: %d of %d" % (decided, total), "warn") if pending
                else chip(decision, "good" if first_word(decision) == "ship" else "bad"))
    codex = r["codex"]
    codex_html = chip("Codex gate: " + (codex or "pending"), "muted")
    meta = []
    if r["base"]:
        meta.append("<div><span>Base</span> %s</div>" % inline(r["base"]))
    head_m = re.search(r"Head:\s*(.+)$", r["base"])
    if head_m:
        meta[-1] = "<div><span>Base</span> %s</div><div><span>Head</span> %s</div>" % (
            inline(r["base"][:head_m.start()].strip()), inline(head_m.group(1)))
    if r["uncommitted"]:
        meta.append('<div class="warn-text"><span>Not reviewed</span> %s</div>' % inline(r["uncommitted"]))
    return """
<header class="hero">
  <div class="title-row"><h1>%s</h1>%s</div>
  <div class="meta">%s</div>
  <div class="grid">
    <div class="card verdict %s"><div class="label">Verdict</div><div class="big">%s</div>
      <div class="sub">%s %s</div></div>
    <div class="card"><div class="label">Confidence</div>
      <div class="meter">%s<strong>%s</strong></div><div class="sub">%s</div></div>
    <div class="card"><div class="label">Findings</div><div class="stats">%s</div>
      <div class="sub">Recommended: %s</div></div>
  </div>
  <div class="summary">%s</div>
</header>""" % (
        inline(r["title"]), '<span class="kicker">Senior Review</span>', "".join(meta),
        verdict_tone(v), inline(v), dec_html, codex_html,
        meter, html.escape(conf_head or "unknown"), inline(conf_rest.strip()),
        stats, html.escape(rec_line or "none"), block(r["summary"]))


def components(r):
    head, rows = r["components"]
    if not rows:
        return ""
    cards = []
    for row in rows:
        row = row + [""] * (4 - len(row))
        name, worst, rec, what = row[:4]
        sev = worst_sev(worst)
        cards.append("""<div class="comp %s"><div class="comp-head"><strong>%s</strong>%s</div>
<div class="comp-rec">%s</div><p>%s</p></div>""" % (
            sev, inline(name), chip(worst or "none", sev), inline(rec), inline(what)))
    return '<div class="comps">%s</div>' % "".join(cards)


def safety(r):
    head, rows = r["safety"]
    if not rows:
        return ""
    cards = []
    for row in rows:
        row = row + [""] * (3 - len(row))
        cards.append('<div class="safe"><div class="label">%s</div><p>%s</p>'
                     '<details><summary>Evidence</summary><p>%s</p></details></div>'
                     % (inline(row[0]), inline(row[1]), inline(row[2])))
    return '<h3>Safety answers</h3><div class="safety">%s</div>' % "".join(cards)


def findings(fs):
    filters = "".join('<button data-filter="%s">%s</button>' % (k, k.title())
                      for k in ("all",) + SEVERITIES + ("accept", "reject", "defer", "pending"))
    rows = []
    for f in fs:
        fl = f["fields"]
        rec, dec = rec_of(f), norm(decision_of(f))
        tags = [f["severity"], "rec-" + rec, ("dec-" + dec) if dec else "pending"]
        rec_text = fl.get("Recommendation", "")
        dec_text = fl.get("Decision", "")
        status = (chip("Decision: " + dec_text, {"accept": "good", "reject": "bad"}.get(dec, "muted"))
                  if dec else chip("Decision pending", "warn"))
        details = "".join(
            '<div class="field"><div class="label">%s</div><div>%s</div></div>'
            % (k, block(fl[k])) for k in FIELD_ORDER
            if k in fl and k not in ("Where", "Recommendation", "Decision") and fl[k])
        rows.append("""
<article class="finding %s" id="f%s" data-tags="%s">
  <div class="f-head">
    <span class="num">#%s</span><span class="sev %s">%s</span>
    <h3>%s</h3>
  </div>
  <div class="f-where">%s</div>%s
  <div class="f-status">%s %s</div>
  <details %s><summary>Details</summary>%s</details>
</article>""" % (
            f["severity"], f["num"], " ".join(tags), f["num"], f["severity"], f["severity"],
            inline(f["title"]), inline(fl.get("Where", "")), teaser(fl.get("Today", "")),
            chip("Recommended: " + rec_text, {"accept": "good", "reject": "bad"}.get(rec, "muted")),
            status, "open" if f["severity"] == "critical" else "", details))
    return '<div class="filters">%s</div><div class="findings">%s</div>' % (filters, "".join(rows))


def teaser(today):
    """The first sentence of Today, so a card says what is wrong while closed."""
    text = " ".join(today.split())
    if not text:
        return ""
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return '<p class="f-today">%s</p>' % inline(m.group(1) if m else text)


def coverage(r):
    if not r["coverage"]:
        return '<p class="empty">%s</p>' % inline(r["coverage_note"] or "No requirement found.")
    icon = {"covered": "&#10003;", "gap": "&#10007;", "partial": "&#9680;"}
    tone = {"covered": "good", "gap": "bad", "partial": "warn"}
    items = "".join('<li class="%s"><span class="ic">%s</span><span>%s</span></li>'
                    % (tone[k], icon[k], inline(t)) for k, t in r["coverage"])
    n = sum(1 for k, _ in r["coverage"] if k == "covered")
    return '<p class="sub">%d of %d covered</p><ul class="checklist">%s</ul>' % (n, len(r["coverage"]), items)


def verification(r):
    head, rows = r["verification"]
    out = []
    if rows:
        tally = {}
        for row in rows:
            t = result_tone(row[1] if len(row) > 1 else "")
            tally[t] = tally.get(t, 0) + 1
        bar = "".join('<i class="%s" style="flex:%d"></i>' % (t, n) for t, n in
                      sorted(tally.items(), key=lambda x: ("good", "warn", "bad").index(x[0])))
        out.append('<div class="vbar">%s</div><p class="sub">%d passed · %d unverified · %d failed</p>'
                   % (bar, tally.get("good", 0), tally.get("warn", 0), tally.get("bad", 0)))
        out.append(simple_table((head, rows), 1))
    if r["staging"]:
        out.append("<h3>Staging checks before production</h3>" + block(r["staging"]))
    return "".join(out) or '<p class="empty">No checks recorded.</p>'


def simple_table(table, chip_col):
    head, rows = table
    th = "".join("<th>%s</th>" % inline(h) for h in head)
    trs = []
    for row in rows:
        tds = []
        for i, c in enumerate(row):
            tds.append("<td>%s</td>" % (chip(c, result_tone(c)) if i == chip_col else inline(c)))
        trs.append("<tr>%s</tr>" % "".join(tds))
    return '<div class="tbl"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
        th, "".join(trs))


CSS = """
:root{--bg:#f7f7f8;--panel:#fff;--ink:#1c1d21;--sub:#5d6170;--line:#e3e4e8;--code:#f1f2f5;
--good:#1a7f45;--good-bg:#e5f5ec;--warn:#9a5b00;--warn-bg:#fdf1dc;--bad:#b42318;--bad-bg:#fde8e6;
--muted:#4b5263;--muted-bg:#eceef2;--accent:#3b5bdb;--add:#e6f6ea;--del:#fdecea}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121317;--panel:#1b1c22;--ink:#e8e9ee;
--sub:#a0a4b2;--line:#2d2f38;--code:#23252d;--good:#4cc38a;--good-bg:#173525;--warn:#f0b35a;--warn-bg:#3a2c14;
--bad:#ff7a6e;--bad-bg:#3d1c1a;--muted:#c2c6d2;--muted-bg:#2a2c35;--accent:#8ea4ff;--add:#173525;--del:#3d1c1a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{overflow-wrap:anywhere;max-width:1080px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0;word-break:break-word}h2{font-size:18px;margin:36px 0 12px}h3{font-size:15px;margin:18px 0 8px}
code{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);padding:1px 5px;border-radius:4px;word-break:break-word}
a{color:var(--accent)}.ref{font-weight:600;text-decoration:none}
.kicker{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--sub)}
.title-row{display:flex;flex-direction:column-reverse;gap:4px}
.meta{display:flex;flex-wrap:wrap;gap:6px 20px;margin:10px 0 16px;color:var(--sub);font-size:13px}
.meta span{font-weight:600;color:var(--ink);margin-right:4px}.warn-text{color:var(--warn)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(240px,100%),1fr));gap:12px}
.card,.comp,.safe,.finding,.tbl,.summary{background:var(--panel);border:1px solid var(--line);border-radius:10px}
.card{padding:14px 16px}.label{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--sub);font-weight:600}
.big{font-size:22px;font-weight:700;margin:4px 0 8px}.sub{color:var(--sub);font-size:13px;margin:6px 0 0}
.verdict.good{border-left:6px solid var(--good)}.verdict.good .big{color:var(--good)}
.verdict.warn{border-left:6px solid var(--warn)}.verdict.warn .big{color:var(--warn)}
.verdict.bad{border-left:6px solid var(--bad)}.verdict.bad .big{color:var(--bad)}
.meter{display:flex;align-items:center;gap:4px;margin:8px 0}.meter i{width:28px;height:10px;border-radius:3px;background:var(--muted-bg)}
.meter i.on.high{background:var(--good)}.meter i.on.medium{background:var(--warn)}.meter i.on.low{background:var(--bad)}
.meter strong{margin-left:8px}
.stats{display:flex;gap:8px;margin:6px 0}.stat{flex:1;text-decoration:none;color:inherit;border-radius:8px;padding:6px 8px;background:var(--muted-bg)}
.stat b{display:block;font-size:22px}.stat span{font-size:12px;text-transform:capitalize}
.stat.critical b{color:var(--bad)}.stat.code b{color:var(--warn)}.stat.trivial b{color:var(--muted)}
.summary{margin-top:12px;padding:4px 16px}
.chip{display:inline-block;font-size:12px;font-weight:600;padding:2px 9px;border-radius:999px;margin:2px 4px 2px 0}
.chip.good{color:var(--good);background:var(--good-bg)}.chip.warn{color:var(--warn);background:var(--warn-bg)}
.chip.bad,.chip.critical{color:var(--bad);background:var(--bad-bg)}.chip.code{color:var(--warn);background:var(--warn-bg)}
.chip.muted,.chip.trivial,.chip.none{color:var(--muted);background:var(--muted-bg)}
.comps{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr));gap:12px}
.comp{padding:12px 14px;border-top:4px solid var(--good)}.comp.critical{border-top-color:var(--bad)}
.comp.code{border-top-color:var(--warn)}.comp.trivial{border-top-color:var(--muted)}
.comp-head{display:flex;justify-content:space-between;gap:8px;align-items:center}
.comp-rec{font-size:13px;font-weight:600;margin-top:4px}.comp p{margin:6px 0 0;font-size:14px;color:var(--sub)}
.safety{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(230px,100%),1fr));gap:12px}
.safe{padding:12px 14px}.safe p{margin:6px 0;font-size:14px}
details summary{cursor:pointer;color:var(--accent);font-size:13px;font-weight:600}
.filters{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.filters button{font:inherit;font-size:13px;padding:4px 12px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:var(--ink);cursor:pointer}
.filters button.on{background:var(--ink);color:var(--panel)}
.findings{display:flex;flex-direction:column;gap:10px}
.finding{min-width:0;padding:12px 16px;border-left:5px solid var(--muted)}.finding.critical{border-left-color:var(--bad)}.finding.code{border-left-color:var(--warn)}
.finding[hidden]{display:none}.f-head{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.f-head h3{margin:0;font-size:15px;flex:1 1 300px}.num{font-weight:700;color:var(--sub)}
.sev{font-size:11px;font-weight:700;text-transform:uppercase;padding:1px 7px;border-radius:4px}
.sev.critical{color:var(--bad);background:var(--bad-bg)}.sev.code{color:var(--warn);background:var(--warn-bg)}.sev.trivial{color:var(--muted);background:var(--muted-bg)}
.f-today{margin:4px 0;font-size:14px}.f-where{font-size:13px;color:var(--sub);margin:4px 0}.f-status{margin:4px 0}
.field{display:grid;grid-template-columns:110px 1fr;gap:10px;padding:8px 0;border-top:1px dashed var(--line)}
.field>div{min-width:0}.field p{margin:0 0 6px}.field ul{margin:0;padding-left:18px}
@media (max-width:600px){.field{grid-template-columns:1fr;gap:2px}}
pre.code{margin:4px 0;padding:8px 0;background:var(--code);border-radius:6px;overflow-x:auto;font:12.5px/1.5 ui-monospace,Menlo,monospace}
pre.code .ln{display:block;padding:0 12px;white-space:pre}.ln.add{background:var(--add)}.ln.del{background:var(--del)}
.checklist{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:6px}
.checklist li{display:flex;gap:10px;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 12px}
.ic{font-weight:700;width:18px;flex:none}.checklist .good .ic{color:var(--good)}.checklist .bad .ic{color:var(--bad)}.checklist .warn .ic{color:var(--warn)}
.vbar{display:flex;height:12px;border-radius:6px;overflow:hidden;gap:2px}.vbar i.good{background:var(--good)}.vbar i.warn{background:var(--warn)}.vbar i.bad{background:var(--bad)}
.tbl{overflow-x:auto;margin-top:10px}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:12px;color:var(--sub)}
tr:last-child td{border-bottom:0}.empty{color:var(--sub)}
nav.toc{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:8px 16px;display:flex;gap:16px;overflow-x:auto;font-size:13px}
nav.toc a{text-decoration:none;color:var(--sub);white-space:nowrap}
"""

JS = """
(function(){
  var btns=document.querySelectorAll('.filters button'), cards=document.querySelectorAll('.finding');
  function apply(tag){
    btns.forEach(function(b){b.classList.toggle('on',b.dataset.filter===tag)});
    cards.forEach(function(c){
      var t=c.dataset.tags.split(' ');
      var hit=tag==='all'||t.indexOf(tag)>=0||t.indexOf('rec-'+tag)>=0||t.indexOf('dec-'+tag)>=0;
      c.hidden=!hit;
    });
  }
  btns.forEach(function(b){b.addEventListener('click',function(){apply(b.dataset.filter)})});
  document.querySelectorAll('.stat').forEach(function(s){s.addEventListener('click',function(){apply(s.dataset.filter)})});
  document.querySelectorAll('a.ref').forEach(function(a){a.addEventListener('click',function(){
    apply('all'); var d=document.querySelector(a.getAttribute('href')+' details'); if(d) d.open=true;})});
  apply('all');
})();
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review: {title}</title><style>{css}</style></head>
<body><nav class="toc"><a href="#top">Summary</a><a href="#changed">What changed</a>
<a href="#findings">Findings</a><a href="#coverage">Requirement</a><a href="#verification">Verification</a></nav>
<main id="top">{body}</main><script>{js}</script></body></html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", help="review.md, or the review folder that holds it")
    ap.add_argument("-o", "--out", help="output path (default: review.html beside the source)")
    args = ap.parse_args(argv)
    src = Path(args.source).expanduser()
    if src.is_dir():
        src = src / "review.md"
    if not src.is_file():
        sys.exit("no review.md at %s" % src)
    out = Path(args.out).expanduser() if args.out else src.with_suffix(".html")
    report = parse(src.read_text(encoding="utf-8"))
    out.write_text(render(report), encoding="utf-8")
    n = len(report["findings"])
    print("wrote %s (%d findings%s)" % (out, n, "" if n else "; none parsed, check the template shape"))


if __name__ == "__main__":
    main()
