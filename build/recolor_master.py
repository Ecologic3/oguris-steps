#!/usr/bin/env python3
"""Recolour the icon artwork's green background to deep purple, keeping
Oguri herself untouched: only pixels that are genuinely green in RGB
(G clearly above R and B) get a hue shift of about +125 degrees, which
lands the sampled dark green (#00321A family) in deep-purple territory
matching her running kit and the Oguri's Alarms purple."""
from PIL import Image
import numpy as np, colorsys, os

APP = os.path.expanduser("~/workspace/steps-app")
SRC = os.path.join(APP, "build", "icon-original.webp")
OUT = os.path.join(APP, "build", "icon-source-purple.png")

img = Image.open(SRC).convert("RGB")
a = np.asarray(img).astype(np.int16)
r, g, b = a[...,0], a[...,1], a[...,2]
greenish = (g > r + 12) & (g >= b + 5)
print("greenish pixels:", int(greenish.sum()), "of", r.size)

hsv = np.asarray(img.convert("HSV")).astype(np.int16)
# PIL hue: 0-255 = 0-360 deg. +89 units ~ +125 deg (green -> purple).
hsv[...,0] = np.where(greenish, (hsv[...,0] + 89) % 256, hsv[...,0])
out = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")
out.save(OUT)
w, h = out.size
samples = [out.getpixel((w//2, int(h*0.03))), out.getpixel((int(w*0.04), h//2)),
           out.getpixel((int(w*0.96), h//2)), out.getpixel((w//2, int(h*0.97)))]
bg = tuple(sum(s[i] for s in samples)//len(samples) for i in range(3))
print("new sampled BG", bg, "#%02X%02X%02X" % bg)
