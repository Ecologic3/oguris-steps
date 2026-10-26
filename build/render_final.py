#!/usr/bin/env python3
"""Final full renders: all approved rules + best entry highlighted in the
list (bold amber, star marker). Daily views highlight the best day; the
weekly view highlights the days of the best week."""
from PIL import Image, ImageDraw, ImageFont
import datetime, os

OUT = os.path.expanduser("~/workspace/steps-app/renders")
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def F(p, s): return ImageFont.truetype(p, s)
BG = (15,20,31); CARD = (27,34,51); WHITE = (255,255,255); MUTED = (148,163,184)
BAR = (46,125,95); HI = (61,220,151); CHIP = (38,47,66); BASE = (51,61,82)
DARKTXT = (11,31,22); AMBER = (240,180,84)
W = 1000
REAL = {19:1950, 20:7200, 21:5100, 22:4300, 23:4600, 24:3900, 25:2800, 26:0}
ROWS = [("Today", 0, True), ("Sun 25 Oct", 2800, False), ("Sat 24 Oct", 3900, False),
        ("Fri 23 Oct", 4600, False), ("Thu 22 Oct", 4300, False), ("Wed 21 Oct", 5100, False),
        ("Tue 20 Oct", 7200, False), ("Mon 19 Oct", 1950, False)]
BESTDAY = "Tue 20 Oct"
BESTWEEK_DAYS = {"Sun 25 Oct","Sat 24 Oct","Fri 23 Oct","Thu 22 Oct","Wed 21 Oct",
                 "Tue 20 Oct","Mon 19 Oct"}

def base(selected, summary):
    H = 1560
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    d.rounded_rectangle([26,26,W-26,H-26], radius=38, fill=CARD)
    d.text((58,52), "History", font=F(BOLD,46), fill=WHITE)
    chips = ["7 DAYS","30 DAYS","90 DAYS","ALL TIME"]
    cw = (W - 116 - 3*18)//4
    for i, name in enumerate(chips):
        x = 58 + i*(cw+18); sel = i == selected
        d.rounded_rectangle([x,128,x+cw,216], radius=44, fill=HI if sel else CHIP)
        tw = d.textlength(name, font=F(BOLD,29))
        d.text((x+(cw-tw)/2,157), name, font=F(BOLD,29), fill=DARKTXT if sel else WHITE)
    y = 244
    for line in summary:
        d.text((58,y), line, font=F(REG,31), fill=MUTED); y += 42
    return img, d, y+18

def axis_label(d, cx, CL, CR, y, text):
    fnt = F(REG,27); tw = d.textlength(text, font=fnt)
    d.text((min(max(cx-tw/2, CL), CR-tw), y), text, font=fnt, fill=MUTED)

def dash_avg(d, CL, CR, y, label, side):
    x = CL
    while x < CR:
        d.line([x, y, min(x+12, CR), y], fill=MUTED, width=2); x += 20
    fnt = F(REG,24); tw = d.textlength(label, font=fnt)
    d.text((CL+4 if side=="left" else CR-tw-4, y-34), label, font=fnt, fill=MUTED)

def rows(d, y, mode):
    for date, steps, is_today in ROWS:
        best = date == BESTDAY
        star = best and date == BESTDAY
        x = 58
        if star:
            d.text((x, y), "★", font=F(BOLD,30), fill=AMBER); x += 44
        d.text((x, y), date, font=F(BOLD if (is_today or best) else REG, 33),
               fill=HI if is_today else (AMBER if best else WHITE))
        s = f"{steps:,}"
        km = f"  {steps*0.00075:.2f} km"
        s_w = d.textlength(s, font=F(BOLD,33)); k_w = d.textlength(km, font=F(REG,29))
        d.text((W-58-k_w-s_w, y), s, font=F(BOLD,33), fill=AMBER if best else WHITE)
        d.text((W-58-k_w, y+2), km, font=F(REG,29), fill=MUTED)
        y += 62
    return y

def save(img, name):
    p = os.path.join(OUT, name); img.save(p); print("wrote", p)

CL, CR = 58, W-58
CH = 424  # chart height

# ---------- 7 days ----------
img, d, top = base(0, ["Last 7 days · Total 27,900 · Daily average 4,650 · Best",
                       "Tue 20 Oct (7,200)"])
CT, CB = top+46, top+46+CH
vals = [REAL[k] for k in (20,21,22,23,24,25,26)]
letters = ["T","W","T","F","S","S","M"]
maxv = max(vals)*1.12; slot = (CR-CL)/len(vals); bw = slot*0.6
dash_avg(d, CL, CR, CB-(CB-CT)*(4650/maxv), "avg 4,650", "right")
for i, v in enumerate(vals):
    cx = CL+slot*i+slot/2; bh = (CB-CT)*(v/maxv)
    if v > 0:
        is_best = v == max(vals)
        col = AMBER if is_best else (HI if i == len(vals)-1 else BAR)
        w2 = bw*1.18 if is_best else bw
        d.rounded_rectangle([cx-w2/2,CB-bh,cx+w2/2,CB], radius=7, fill=col)
        d.rectangle([cx-w2/2,CB-7,cx+w2/2,CB], fill=col)
        t = f"{v:,}"
        fnt = F(BOLD,27) if is_best else F(REG,26)
        tw = d.textlength(t, font=fnt)
        d.text((cx-tw/2, CB-bh-36), t, font=fnt, fill=AMBER if is_best else WHITE)
d.line([CL,CB,CR,CB], fill=BASE, width=2)
for i, lab in enumerate(letters):
    axis_label(d, CL+slot*i+slot/2, CL, CR, CB+12, lab)
rows(d, CB+66, "day")
save(img, "final-7d.png")

# ---------- 30 days ----------
img, d, top = base(1, ["Last 30 days · Total 29,850 · Daily average 4,264 · Best",
                       "Tue 20 Oct (7,200)"])
CT, CB = top+46, top+46+CH
start = datetime.date(2026,9,27); vals = []
for i in range(30):
    dt = start + datetime.timedelta(days=i)
    vals.append(REAL.get(dt.day,0) if dt.month == 10 else 0)
maxv = max(vals)*1.12; slot = (CR-CL)/30.0; bw = max(8, slot*0.58)
dash_avg(d, CL, CR, CB-(CB-CT)*(4264/maxv), "avg 4,264", "left")
for i, v in enumerate(vals):
    cx = CL+slot*i+slot/2; bh = (CB-CT)*(v/maxv)
    if v > 0:
        is_best = v == max(vals)
        col = AMBER if is_best else BAR
        w2 = bw*1.25 if is_best else bw
        d.rounded_rectangle([cx-w2/2,CB-bh,cx+w2/2,CB], radius=5, fill=col)
        d.rectangle([cx-w2/2,CB-5,cx+w2/2,CB], fill=col)
    if v == max(vals):
        t = f"{v:,}"; tw = d.textlength(t, font=F(BOLD,26))
        d.text((cx-tw/2, CB-bh-36), t, font=F(BOLD,26), fill=AMBER)
d.line([CL,CB,CR,CB], fill=BASE, width=2)
for i in (0,6,13,20,29):
    dt = start + datetime.timedelta(days=i)
    axis_label(d, CL+slot*i+slot/2, CL, CR, CB+12, dt.strftime("%d %b").lstrip("0"))
rows(d, CB+66, "day")
save(img, "final-30d.png")

# ---------- 90 days weekly ----------
img, d, top = base(2, ["Last 90 days · Total 29,850 · Daily average 4,264 · Best",
                       "Tue 20 Oct (7,200)"])
CT, CB = top+46, top+46+CH
weeks = []; monday = datetime.date(2026,7,27)
while monday <= datetime.date(2026,10,26):
    tot = 0
    for k in range(7):
        dt = monday + datetime.timedelta(days=k)
        if dt.month == 10 and dt.day in REAL: tot += REAL[dt.day]
    weeks.append((monday.strftime("%d %b").lstrip("0"), tot))
    monday += datetime.timedelta(days=7)
maxv = max(t for _,t in weeks)*1.15; slot = (CR-CL)/len(weeks); bw = slot*0.58
rec = [t for _,t in weeks if t > 0]; wavg = sum(rec)/len(rec)
dash_avg(d, CL, CR, CB-(CB-CT)*(wavg/maxv), "avg 29.9k", "left")
for i,(lab,v) in enumerate(weeks):
    cx = CL+slot*i+slot/2; bh = (CB-CT)*(v/maxv)
    if v > 0:
        is_best = v == max(t for _, t in weeks)
        col = AMBER if is_best else BAR
        w2 = bw*1.18 if is_best else bw
        d.rounded_rectangle([cx-w2/2,CB-bh,cx+w2/2,CB], radius=6, fill=col)
        d.rectangle([cx-w2/2,CB-6,cx+w2/2,CB], fill=col)
        t = f"{v/1000:.1f}k"; tw = d.textlength(t, font=F(BOLD,26))
        d.text((cx-tw/2, CB-bh-36), t, font=F(BOLD,26), fill=AMBER if is_best else WHITE)
d.line([CL,CB,CR,CB], fill=BASE, width=2)
for i,(lab,v) in enumerate(weeks):
    if i % 2 == 0: axis_label(d, CL+slot*i+slot/2, CL, CR, CB+12, lab)
rows(d, CB+66, "week")
save(img, "final-90d.png")

# ---------- All time ----------
img, d, top = base(3, ["All time · Total 29,850 · Daily average 4,264 · Best Tue",
                       "20 Oct (7,200)"])
CT, CB = top+46, top+46+CH
vals = [REAL[k] for k in sorted(REAL)]
maxv = max(vals)*1.12; slot = (CR-CL)/len(vals); bw = slot*0.6
dash_avg(d, CL, CR, CB-(CB-CT)*(4264/maxv), "avg 4,264", "left")
for i, v in enumerate(vals):
    cx = CL+slot*i+slot/2; bh = (CB-CT)*(v/maxv)
    if v > 0:
        is_best = v == max(vals)
        col = AMBER if is_best else (HI if i == len(vals)-1 else BAR)
        w2 = bw*1.18 if is_best else bw
        d.rounded_rectangle([cx-w2/2,CB-bh,cx+w2/2,CB], radius=7, fill=col)
        d.rectangle([cx-w2/2,CB-7,cx+w2/2,CB], fill=col)
        t = f"{v:,}"
        fnt = F(BOLD,27) if is_best else F(REG,26)
        tw = d.textlength(t, font=fnt)
        d.text((cx-tw/2, CB-bh-36), t, font=fnt, fill=AMBER if is_best else WHITE)
d.line([CL,CB,CR,CB], fill=BASE, width=2)
for i in (0,3,len(vals)-1):
    dt = datetime.date(2026,10,19) + datetime.timedelta(days=i)
    axis_label(d, CL+slot*i+slot/2, CL, CR, CB+12, dt.strftime("%d %b").lstrip("0"))
rows(d, CB+66, "day")
save(img, "final-all.png")
