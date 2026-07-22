from PIL import Image, ImageFilter, ImageEnhance

SRC = "/home/user/foto/source_fixed.jpg"   # left text realigned to right block level
OUT_PNG = "/home/user/foto/vk_cover_design_1920x768.png"
OUT_JPG = "/home/user/foto/vk_cover_design_1920x768.jpg"

W, H = 1920, 768
CONTENT_W = 1240          # keeps text span inside VK mobile+desktop safe zone
src = Image.open(SRC).convert("RGB")
sw, sh = src.size

# --- 1. Full-bleed blurred background (cover), biased downward to landscape ---
scale = max(W / sw, H / sh)
bw, bh = round(sw * scale), round(sh * scale)
bg = src.resize((bw, bh), Image.LANCZOS)
left = (bw - W) // 2
top = int((bh - H) * 0.08)   # keep top = blurred SKY; blurred figure stays mid, hidden behind sharp portrait
bg = bg.crop((left, top, left + W, top + H))
bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
bg = ImageEnhance.Brightness(bg).enhance(1.02)   # matched, no big step at the seam

# --- 2. Sharp content fitted by WIDTH, BOTTOM-aligned (woman grounded) ---
fscale = CONTENT_W / sw
fw, fh = CONTENT_W, round(sh * fscale)   # 1240 x ~680
fg = src.resize((fw, fh), Image.LANCZOS)
ox = (W - fw) // 2
oy = H - fh                              # bottom edge flush with canvas bottom

# --- 3. Feather TOP + LEFT + RIGHT only (bottom bleeds off the canvas) ---
F = 85
alpha = Image.new("L", (fw, fh), 255)
px = alpha.load()
for x in range(fw):
    for y in range(fh):
        d = min(x, fw - 1 - x, y)        # no bottom term -> hard bottom bleed
        px[x, y] = 255 if d >= F else int(255 * d / F)

canvas = bg.copy()
canvas.paste(fg, (ox, oy), alpha)

# --- 4. Airy top-corner light lift (echoes original hazy corners) ---
lift = Image.new("L", (W, H), 0)
lpx = lift.load()
cw = 300
for x in range(cw):
    fx = 1 - x / cw
    for y in range(H):
        fy = max(0.0, 1 - y / (H * 0.5))
        v = int(50 * fx * fy)
        lpx[x, y] = v
        lpx[W - 1 - x, y] = v
bright = ImageEnhance.Brightness(canvas).enhance(1.12)
canvas = Image.composite(bright, canvas, lift)

canvas = canvas.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=2))

canvas.save(OUT_PNG)
canvas.convert("RGB").save(OUT_JPG, quality=92)
print("saved", canvas.size, "content", (fw, fh), "at", (ox, oy),
      "side margins", ox, "top strip", oy)
