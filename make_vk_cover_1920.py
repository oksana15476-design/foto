from PIL import Image, ImageFilter, ImageEnhance

SRC = "/home/user/foto/source.jpg"
OUT_PNG = "/home/user/foto/vk_cover_design_1920x768.png"
OUT_JPG = "/home/user/foto/vk_cover_design_1920x768.jpg"

W, H = 1920, 768
src = Image.open(SRC).convert("RGB")
sw, sh = src.size  # 1280 x 702

# --- 1. Background: "cover" the full canvas, biased downward (more forest/river, less sky-haze) ---
scale = max(W / sw, H / sh)                     # 1.5
bw, bh = round(sw * scale), round(sh * scale)   # 1920 x 1053
bg = src.resize((bw, bh), Image.LANCZOS)
left = (bw - W) // 2                            # 0  -> keeps x-alignment (left=forest, right=waterfall)
top = int((bh - H) * 0.72)                      # bias down
bg = bg.crop((left, top, left + W, top + H))
bg = bg.filter(ImageFilter.GaussianBlur(radius=34))
bg = ImageEnhance.Brightness(bg).enhance(1.06)
bg = ImageEnhance.Contrast(bg).enhance(0.96)

# --- 2. Sharp full banner fitted by HEIGHT (nothing cropped) ---
fscale = H / sh
fw, fh = round(sw * fscale), H                  # ~1400 x 768
fg = src.resize((fw, fh), Image.LANCZOS)

# --- 3. Feathered alpha so sharp edges melt into the extension ---
F = 85
alpha = Image.new("L", (fw, fh), 255)
px = alpha.load()
for x in range(F):
    v = int(255 * (x / F))
    for y in range(fh):
        px[x, y] = v
        px[fw - 1 - x, y] = v

# --- 4. Composite centered ---
canvas = bg.copy()
ox = (W - fw) // 2                              # ~260
canvas.paste(fg, (ox, 0), alpha)

# --- 5. Airy top-corner light lift (echoes original hazy corners, no blob) ---
lift = Image.new("L", (W, H), 0)
lpx = lift.load()
cw = 300
for x in range(cw):
    fx = 1 - x / cw
    for y in range(H):
        fy = max(0.0, 1 - y / (H * 0.55))       # only upper part
        v = int(70 * fx * fy)
        lpx[x, y] = v
        lpx[W - 1 - x, y] = v
bright = ImageEnhance.Brightness(canvas).enhance(1.16)
canvas = Image.composite(bright, canvas, lift)

# --- 6. Whisper-soft vignette on far edges ---
vig = Image.new("L", (W, H), 255)
vpx = vig.load()
edge = 160
for x in range(edge):
    v = int(255 * (0.93 + 0.07 * (x / edge)))
    for y in range(H):
        vpx[x, y] = v
        vpx[W - 1 - x, y] = v
dark = ImageEnhance.Brightness(canvas).enhance(0.92)
canvas = Image.composite(canvas, dark, vig)

# --- 7. Keep portrait crisp ---
canvas = canvas.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))

canvas.save(OUT_PNG)
canvas.convert("RGB").save(OUT_JPG, quality=92)
print("saved", canvas.size, "sharp block", (fw, fh), "at x", ox, "side margins", ox)
