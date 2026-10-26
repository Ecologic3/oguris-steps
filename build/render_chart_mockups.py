#!/usr/bin/env python3
"""Mockup renders of the proposed fixed History charts, using sample
imported data (19-26 Oct 2026) from his screenshots. Design rules:
- Value labels only when bars are sparse (<=14 bars) or only the best bar.
- Axis labels are real dates (d MMM), edge-clamped, never day-numbers.
- 90 days aggregates to calendar-week bars with totals in k.
- 30 days keeps daily bars, adds a dashed daily-average line for scale.
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.expanduser("~/workspace/steps-app/renders")
os.makedirs(OUT, exist_ok=True)
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def F(path, s): return ImageFont.truetype(path, s)

BG = (15, 20, 31); CARD = (27, 34, 51); WHITE = (255, 255, 255)
MUTED = (148, 163, 184); BAR = (46, 125, 95); HI = (61, 220, 151)
CHIP = (38, 47, 66); BASE = (51, 61, 82); DARKTXT = (11, 31, 22)
W = 1000

def card_base(selected, summary_lines, sample=False):
    H = 1180
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([26, 26, W-26, H-26], radius=38, fill=CARD)
    d.text((58, 52), "History", font=F(BOLD, 46), fill=WHITE)
    if sample:
        tw = d.textlength("SAMPLE DATA", font=F(BOLD, 24))
        d.rounded_rectangle([W-58-tw-28, 56, W-58+8, 100], radius=12, outline=HI, width=2)
        d.text((W-58-tw-14, 66), "SAMPLE DATA", font=F(BOLD, 24), fill=HI)
    chips = ["7 DAYS", "30 DAYS", "90 DAYS", "ALL TIME"]
    cw = (W - 116 - 3*18) // 4
    for i, name in enumerate(chips):
        x = 58 + i * (cw + 18)
        sel = i == selected
        d.rounded_rectangle([x, 128, x+cw, 216], radius=44,
                            fill=HI if sel else CHIP)
        t = name; fnt = F(BOLD, 29)
        tw = d.textlength(t, font=fnt)
        d.text((x + (cw-tw)/2, 157), t, font=fnt, fill=DARKTXT if sel else WHITE)
    y = 244
    for line in summary_lines:
        d.text((58, y), line, font=F(REG, 31), fill=MUTED); y += 42
    return img, d, y + 18

def axis_label(d, cx, chart_left, chart_right, y, text):
    fnt = F(REG, 27); tw = d.textlength(text, font=fnt)
    x = min(max(cx - tw/2, chart_left), chart_right - tw)
    d.text((x, y), text, font=fnt, fill=MUTED)

def list_rows(d, y):
    rows = [("Today", "0", "0.00 km", True),
            ("Sun 25 Oct", "2,800", "2.10 km", False),
            ("Sat 24 Oct", "3,900", "2.93 km", False)]
    for date, steps, km, is_today in rows:
        d.text((58, y), date, font=F(BOLD if is_today else REG, 33),
               fill=HI if is_today else WHITE)
        s_w = d.textlength(steps, font=F(BOLD, 33))
        k_w = d.textlength("  " + km, font=F(REG, 29))
        d.text((W-58-k_w-s_w, y), steps, font=F(BOLD, 33), fill=WHITE)
        d.text((W-58-k_w, y+2), "  " + km, font=F(REG, 29), fill=MUTED)
        y += 62
    return y

def finish(img, name):
    p = os.path.join(OUT, name); img.save(p); print("wrote", p)

REAL = {19: 1950, 20: 7200, 21: 5100, 22: 4300, 23: 4600, 24: 3900, 25: 2800, 26: 0}

# ---------- 30 days, daily, real data ----------
img, d, top = card_base(1, ["Last 30 days · Total 29,850 · Daily average 4,264 · Best",
                            "Tue 20 Oct (7,200)"])
CL, CR = 58, W-58; CT, CB = top + 46, top + 470
days = list(range(27, 31)) + list(range(1, 27))          # Sep 27 .. Oct 26
vals = [REAL.get(day, 0) if day >= 19 and not (day > 26) else 0 for day in days]
vals = []
import datetime
start = datetime.date(2026, 9, 27)
for i in range(30):
    dt = start + datetime.timedelta(days=i)
    vals.append(REAL.get(dt.day, 0) if dt.month == 10 else 0)
maxv = max(vals) * 1.12
slot = (CR - CL) / 30.0; bw = max(8, slot * 0.58)
avg = 4264
ay = CB - (CB - CT) * (avg / maxv)
x = CL
while x < CR:  # dashed average line
    d.line([x, ay, min(x + 12, CR), ay], fill=MUTED, width=2); x += 20
d.text((CL + 4, ay - 34), "avg 4,264", font=F(REG, 24), fill=MUTED)
for i, v in enumerate(vals):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    if v > 0:
        d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=5, fill=BAR)
        d.rectangle([cx-bw/2, CB-5, cx+bw/2, CB], fill=BAR)
    if v == max(vals):
        t = f"{v:,}"
        tw = d.textlength(t, font=F(BOLD, 26))
        d.text((cx - tw/2, CB - bh - 36), t, font=F(BOLD, 26), fill=WHITE)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i in (0, 6, 13, 20, 29):
    dt = start + datetime.timedelta(days=i)
    axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, dt.strftime("%d %b").lstrip("0"))
list_rows(d, CB + 66)
finish(img, "chart-30d-real.png")

# ---------- 90 days, weekly, real data ----------
img, d, top = card_base(2, ["Last 90 days · Total 29,850 · Daily average 4,264 · Best",
                            "Tue 20 Oct (7,200)"])
CT, CB = top + 46, top + 470
weeks = []  # (label, total)
monday = datetime.date(2026, 7, 27)
while monday <= datetime.date(2026, 10, 26):
    total = 0
    for k in range(7):
        dt = monday + datetime.timedelta(days=k)
        if dt.month == 10 and dt.day in REAL: total += REAL[dt.day]
    weeks.append((monday.strftime("%d %b").lstrip("0"), total))
    monday += datetime.timedelta(days=7)
maxv = max(t for _, t in weeks) * 1.15
slot = (CR - CL) / len(weeks); bw = slot * 0.58
for i, (lab, v) in enumerate(weeks):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    if v > 0:
        col = HI if i == len(weeks) - 1 else BAR
        d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=6, fill=col)
        d.rectangle([cx-bw/2, CB-6, cx+bw/2, CB], fill=col)
        t = f"{v/1000:.1f}k"
        tw = d.textlength(t, font=F(BOLD, 26))
        d.text((cx - tw/2, CB - bh - 36), t, font=F(BOLD, 26), fill=WHITE)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i, (lab, v) in enumerate(weeks):
    if i % 2 == 0 or (i == len(weeks) - 1 and i % 2 == 1 and False):
        axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, lab)
list_rows(d, CB + 66)
finish(img, "chart-90d-weekly-real.png")

# ---------- 90 days, weekly, SAMPLE data ----------
img, d, top = card_base(2, ["Last 90 days · Total 307,900 · Daily average 3,421 · Best",
                            "Wed 14 Oct (7,930)"], sample=True)
CT, CB = top + 46, top + 470
sample_weeks = [15.4, 21.9, 18.2, 24.6, 28.1, 19.7, 23.3, 29.8, 21.2, 17.6, 25.4, 26.2, 30.1, 6.5]
labels = []
monday = datetime.date(2026, 7, 27)
for i in range(len(sample_weeks)):
    labels.append((monday + datetime.timedelta(days=7*i)).strftime("%d %b").lstrip("0"))
maxv = max(sample_weeks) * 1.18
slot = (CR - CL) / len(sample_weeks); bw = slot * 0.58
for i, v in enumerate(sample_weeks):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    col = HI if i == len(sample_weeks) - 1 else BAR
    d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=6, fill=col)
    d.rectangle([cx-bw/2, CB-6, cx+bw/2, CB], fill=col)
    t = f"{v:.1f}k"
    tw = d.textlength(t, font=F(REG, 23))
    d.text((cx - tw/2, CB - bh - 32), t, font=F(REG, 23), fill=WHITE)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i, lab in enumerate(labels):
    if i % 2 == 0:
        axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, lab)
list_rows(d, CB + 66)
finish(img, "chart-90d-weekly-sample.png")

# ---------- All time, daily, real data ----------
img, d, top = card_base(3, ["All time · Total 29,850 · Daily average 4,264 · Best Tue",
                            "20 Oct (7,200)"])
CT, CB = top + 46, top + 470
vals = [REAL[k] for k in sorted(REAL)]
maxv = max(vals) * 1.12
slot = (CR - CL) / len(vals); bw = slot * 0.6
for i, v in enumerate(vals):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    if v > 0:
        col = HI if i == len(vals) - 1 else BAR
        d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=7, fill=col)
        d.rectangle([cx-bw/2, CB-7, cx+bw/2, CB], fill=col)
        t = f"{v:,}"
        tw = d.textlength(t, font=F(REG, 26))
        d.text((cx - tw/2, CB - bh - 36), t, font=F(REG, 26), fill=WHITE)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i in (0, 3, len(vals) - 1):
    dt = datetime.date(2026, 10, 19) + datetime.timedelta(days=i)
    axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, dt.strftime("%d %b").lstrip("0"))
list_rows(d, CB + 66)
finish(img, "chart-alltime-real.png")

# ---------- 7 days, daily, real data (unchanged design) ----------
img, d, top = card_base(0, ["Last 7 days · Total 27,900 · Daily average 4,650 · Best",
                            "Tue 20 Oct (7,200)"])
CT, CB = top + 46, top + 470
vals7 = [REAL[k] for k in (20, 21, 22, 23, 24, 25, 26)]
letters = ["T", "W", "T", "F", "S", "S", "M"]
maxv = max(vals7) * 1.12
slot = (CR - CL) / len(vals7); bw = slot * 0.6
for i, v in enumerate(vals7):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    if v > 0:
        col = HI if i == len(vals7) - 1 else BAR
        d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=7, fill=col)
        d.rectangle([cx-bw/2, CB-7, cx+bw/2, CB], fill=col)
        t = f"{v:,}"
        tw = d.textlength(t, font=F(REG, 26))
        d.text((cx - tw/2, CB - bh - 36), t, font=F(REG, 26), fill=WHITE)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i, lab in enumerate(letters):
    axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, lab)
list_rows(d, CB + 66)
finish(img, "chart-7d-real.png")

# ================= v3: rolling average + tap-to-inspect =================
AMBER = (240, 180, 84)

def rolling_points(vals_window, recorded):
    """Trailing 7-day average over recorded days only. vals_window is the
    30 daily values; recorded is a set of indexes that have data (today
    excluded). Returns list of (index, value)."""
    pts = []
    for i in range(len(vals_window)):
        tot = 0; n = 0
        for j in range(max(0, i - 6), i + 1):
            if j in recorded:
                tot += vals_window[j]; n += 1
        if n > 0 and i in recorded:
            pts.append((i, tot / n))
    return pts

def draw_30d(selected=None):
    img, d, top = card_base(1, ["Last 30 days · Total 29,850 · Daily average 4,264 · Best",
                                "Tue 20 Oct (7,200)"])
    CL, CR = 58, W - 58
    pill_h = 0
    if selected is not None:
        pill_h = 58
        label = selected[0]
        tw = d.textlength(label, font=F(REG, 28))
        d.rounded_rectangle([CL, top + 2, CL + tw + 36, top + 48], radius=23, fill=CHIP)
        d.text((CL + 18, top + 10), label, font=F(REG, 28), fill=WHITE)
    CT, CB = top + pill_h + 46, top + pill_h + 470
    import datetime as _dt
    start = _dt.date(2026, 9, 27)
    vals = []
    recorded = set()
    for i in range(30):
        dt = start + _dt.timedelta(days=i)
        v = REAL.get(dt.day, 0) if dt.month == 10 else 0
        vals.append(v)
        if dt.month == 10 and dt.day in REAL and dt.day != 26:
            recorded.add(i)
    maxv = max(vals) * 1.12
    slot = (CR - CL) / 30.0; bw = max(8, slot * 0.58)
    sel_idx = selected[1] if selected is not None else -1
    for i, v in enumerate(vals):
        cx = CL + slot * i + slot / 2
        bh = (CB - CT) * (v / maxv)
        if v > 0:
            col = HI if i == sel_idx else BAR
            d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=5, fill=col)
            d.rectangle([cx-bw/2, CB-5, cx+bw/2, CB], fill=col)
        if v == max(vals) and sel_idx < 0:
            t = f"{v:,}"
            tw = d.textlength(t, font=F(BOLD, 26))
            d.text((cx - tw/2, CB - bh - 36), t, font=F(BOLD, 26), fill=WHITE)
    # rolling 7-day average curve (amber), ending yesterday
    pts = rolling_points(vals, recorded)
    xy = []
    for i, av in pts:
        x = CL + slot * i + slot / 2
        y = CB - (CB - CT) * (av / maxv)
        xy.append((x, y))
    for a, b in zip(xy, xy[1:]):
        d.line([a, b], fill=AMBER, width=4)
    for (x, y) in xy:
        d.ellipse([x-5, y-5, x+5, y+5], fill=AMBER)
    d.text((CL + 4, CT - 34), "7-day average", font=F(REG, 24), fill=AMBER)
    d.line([CL, CB, CR, CB], fill=BASE, width=2)
    for i in (0, 6, 13, 20, 29):
        dt = start + _dt.timedelta(days=i)
        axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, dt.strftime("%d %b").lstrip("0"))
    list_rows(d, CB + 66)
    return img

finish(draw_30d(), "chart-30d-roll.png")
# Oct 21 is index: Sep27=0 ... Oct 21 = 24
finish(draw_30d(("Wed 21 Oct · 5,100 steps · 3.83 km", 24)), "chart-30d-tap.png")

# ---------- 90 days weekly, tapped state ----------
img, d, top = card_base(2, ["Last 90 days · Total 29,850 · Daily average 4,264 · Best",
                            "Tue 20 Oct (7,200)"])
CL, CR = 58, W - 58
label = "Week of 19 Oct · 29,850 steps · 22.39 km"
tw = d.textlength(label, font=F(REG, 28))
d.rounded_rectangle([CL, top + 2, CL + tw + 36, top + 48], radius=23, fill=CHIP)
d.text((CL + 18, top + 10), label, font=F(REG, 28), fill=WHITE)
CT, CB = top + 58 + 46, top + 58 + 470
import datetime as _dt2
weeks = []
monday = _dt2.date(2026, 7, 27)
while monday <= _dt2.date(2026, 10, 26):
    total = 0
    for k in range(7):
        dt = monday + _dt2.timedelta(days=k)
        if dt.month == 10 and dt.day in REAL: total += REAL[dt.day]
    weeks.append((monday.strftime("%d %b").lstrip("0"), total))
    monday += _dt2.timedelta(days=7)
maxv = max(t for _, t in weeks) * 1.15
slot = (CR - CL) / len(weeks); bw = slot * 0.58
for i, (lab, v) in enumerate(weeks):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    if v > 0:
        col = HI if lab == "19 Oct" else BAR
        d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=6, fill=col)
        d.rectangle([cx-bw/2, CB-6, cx+bw/2, CB], fill=col)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i, (lab, v) in enumerate(weeks):
    if i % 2 == 0:
        axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, lab)
list_rows(d, CB + 66)
finish(img, "chart-90d-tap.png")

# ================= v4: dashed average line on ALL views =================
def dash_avg(d, CL, CR, y, label, label_side):
    x = CL
    while x < CR:
        d.line([x, y, min(x + 12, CR), y], fill=MUTED, width=2); x += 20
    fnt = F(REG, 24)
    tw = d.textlength(label, font=fnt)
    lx = CL + 4 if label_side == "left" else CR - tw - 4
    d.text((lx, y - 34), label, font=fnt, fill=MUTED)

# ---- 7 days with avg line (avg over recorded days in window: 4,650) ----
img, d, top = card_base(0, ["Last 7 days · Total 27,900 · Daily average 4,650 · Best",
                            "Tue 20 Oct (7,200)"])
CT, CB = top + 46, top + 470
vals7 = [REAL[k] for k in (20, 21, 22, 23, 24, 25, 26)]
letters = ["T", "W", "T", "F", "S", "S", "M"]
maxv = max(vals7) * 1.12
slot = (CR - CL) / len(vals7); bw = slot * 0.6
dash_avg(d, CL, CR, CB - (CB - CT) * (4650 / maxv), "avg 4,650", "right")
for i, v in enumerate(vals7):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    if v > 0:
        col = HI if i == len(vals7) - 1 else BAR
        d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=7, fill=col)
        d.rectangle([cx-bw/2, CB-7, cx+bw/2, CB], fill=col)
        t = f"{v:,}"
        tw = d.textlength(t, font=F(REG, 26))
        d.text((cx - tw/2, CB - bh - 36), t, font=F(REG, 26), fill=WHITE)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i, lab in enumerate(letters):
    axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, lab)
list_rows(d, CB + 66)
finish(img, "chart-7d-avg.png")

# ---- All time with avg line (4,264) ----
img, d, top = card_base(3, ["All time · Total 29,850 · Daily average 4,264 · Best Tue",
                            "20 Oct (7,200)"])
CT, CB = top + 46, top + 470
vals = [REAL[k] for k in sorted(REAL)]
maxv = max(vals) * 1.12
slot = (CR - CL) / len(vals); bw = slot * 0.6
dash_avg(d, CL, CR, CB - (CB - CT) * (4264 / maxv), "avg 4,264", "left")
for i, v in enumerate(vals):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    if v > 0:
        col = HI if i == len(vals) - 1 else BAR
        d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=7, fill=col)
        d.rectangle([cx-bw/2, CB-7, cx+bw/2, CB], fill=col)
        t = f"{v:,}"
        tw = d.textlength(t, font=F(REG, 26))
        d.text((cx - tw/2, CB - bh - 36), t, font=F(REG, 26), fill=WHITE)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i in (0, 3, len(vals) - 1):
    dt = datetime.date(2026, 10, 19) + datetime.timedelta(days=i)
    axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, dt.strftime("%d %b").lstrip("0"))
list_rows(d, CB + 66)
finish(img, "chart-alltime-avg.png")

# ---- 90 days weekly with avg line (weekly avg over recorded weeks) ----
img, d, top = card_base(2, ["Last 90 days · Total 29,850 · Daily average 4,264 · Best",
                            "Tue 20 Oct (7,200)"])
CT, CB = top + 46, top + 470
weeks = []
monday = datetime.date(2026, 7, 27)
while monday <= datetime.date(2026, 10, 26):
    total = 0
    for k in range(7):
        dt = monday + datetime.timedelta(days=k)
        if dt.month == 10 and dt.day in REAL: total += REAL[dt.day]
    weeks.append((monday.strftime("%d %b").lstrip("0"), total))
    monday += datetime.timedelta(days=7)
maxv = max(t for _, t in weeks) * 1.15
slot = (CR - CL) / len(weeks); bw = slot * 0.58
rec = [t for _, t in weeks if t > 0]
wavg = sum(rec) / len(rec)
dash_avg(d, CL, CR, CB - (CB - CT) * (wavg / maxv), "avg 29.9k", "left")
for i, (lab, v) in enumerate(weeks):
    cx = CL + slot * i + slot / 2
    bh = (CB - CT) * (v / maxv)
    if v > 0:
        d.rounded_rectangle([cx-bw/2, CB-bh, cx+bw/2, CB], radius=6, fill=BAR)
        d.rectangle([cx-bw/2, CB-6, cx+bw/2, CB], fill=BAR)
        t = f"{v/1000:.1f}k"
        tw = d.textlength(t, font=F(BOLD, 26))
        d.text((cx - tw/2, CB - bh - 36), t, font=F(BOLD, 26), fill=WHITE)
d.line([CL, CB, CR, CB], fill=BASE, width=2)
for i, (lab, v) in enumerate(weeks):
    if i % 2 == 0:
        axis_label(d, CL + slot * i + slot / 2, CL, CR, CB + 12, lab)
list_rows(d, CB + 66)
finish(img, "chart-90d-avg.png")
