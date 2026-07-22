from PIL import Image, ImageFilter, ImageEnhance

SRC = "/home/user/foto/source.jpg"
OUT_PNG = "/home/user/foto/vk_cover_1590x400.png"
OUT_JPG = "/home/user/foto/vk_cover_1590x400.jpg"

W, H = 1590, 400
src = Image.open(SRC).convert("RGB")
sw, sh = src.size  # 1280 x 702

# --- 1. Blurred background that COVERs the whole 1590x400 canvas ---
scale = max(W / sw, H / sh)
bw, bh = round(sw * scale), round(sh * scale)
bg = src.resize((bw, bh), Image.LANCZOS)
# center-crop to canvas
left = (bw - W) // 2
top = (bh - H) // 2
bg = bg.crop((left, top, left + W, top + H))
bg = bg.filter(ImageFilter.GaussianBlur(radius=46))
# lighten a touch to keep the airy, hazy feel of the original corners
bg = ImageEnhance.Brightness(bg).enhance(1.08)
bg = ImageEnhance.Contrast(bg).enhance(0.95)

# --- 2. Sharp full banner fitted by HEIGHT (nothing cropped) ---
fscale = H / sh
fw, fh = round(sw * fscale), H  # ~729 x 400
fg = src.resize((fw, fh), Image.LANCZOS)

# --- 3. Feathered alpha so sharp edges melt into the blurred background ---
F = 55  # feather width in px on each side
alpha = Image.new("L", (fw, fh), 255)
px = alpha.load()
for x in range(F):
    v = int(255 * (x / F))
    for y in range(fh):
        px[x, y] = v            # left ramp 0->255
        px[fw - 1 - x, y] = v   # right ramp 255->0

# --- 4. Composite centered ---
canvas = bg.copy()
ox = (W - fw) // 2
canvas.paste(fg, (ox, 0), alpha)

# --- 5. Gentle side vignette to smooth far edges ---
vig = Image.new("L", (W, H), 255)
vpx = vig.load()
edge = 120
for x in range(edge):
    v = int(255 * (0.75 + 0.25 * (x / edge)))  # darken far edges to ~75%
    for y in range(H):
        vpx[x, y] = v
        vpx[W - 1 - x, y] = v
dark = ImageEnhance.Brightness(canvas).enhance(0.9)
canvas = Image.composite(canvas, dark, vig)

canvas.save(OUT_PNG)
canvas.convert("RGB").save(OUT_JPG, quality=92)
print("saved", canvas.size)
