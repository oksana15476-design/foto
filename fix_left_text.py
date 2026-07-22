import numpy as np
from PIL import Image

SRC = "/home/user/foto/source.jpg"
OUT = "/home/user/foto/source_fixed.jpg"
DY = 45  # shift left block down so top of "Елена" aligns with top of "Помогаю выйти"

# left text block region (x0,x1,y0,y1)
X0, X1, Y0, Y1 = 56, 476, 96, 384

img = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float64)
H, W, _ = img.shape

def lum(a):
    return a @ np.array([0.299, 0.587, 0.114])

# --- 1. text alpha matte inside region (dark glyphs on light sky) ---
sub = img[Y0:Y1, X0:X1]
ls = lum(sub)

# text mask (generous, to catch anti-aliased halos), then dilate a few px
mask = ls < 165.0
def dilate(m):
    return (m | np.roll(m, 1, 0) | np.roll(m, -1, 0)
              | np.roll(m, 1, 1) | np.roll(m, -1, 1))
for _ in range(3):
    mask = dilate(mask)

# harmonic (Laplace) inpaint of the masked area -> clean background plate
plate = sub.copy()
bright_mean = sub[~mask].mean(axis=0)
plate[mask] = bright_mean
mk = mask.astype(np.float64)[..., None]
for _ in range(1200):
    up    = np.roll(plate, -1, axis=0)
    down  = np.roll(plate,  1, axis=0)
    left  = np.roll(plate, -1, axis=1)
    right = np.roll(plate,  1, axis=1)
    avg = (up + down + left + right) / 4.0
    plate = plate * (1 - mk) + avg * mk

# --- 2. continuous alpha from how much darker orig is vs clean plate ---
lp = lum(plate)
alpha = np.clip((lp - ls) / 60.0, 0.0, 1.0)   # 1 on solid glyph, 0 on background

# --- 3. build full-size clean base (region replaced by plate) and text layer ---
from PIL import ImageFilter
base = img.copy()
base[Y0:Y1, X0:X1] = plate
# smooth faint diffusion speckle in the (mostly sky) vacated area, background only
sky_y1 = Y0 + 170
patch = Image.fromarray(np.clip(base[Y0:sky_y1, X0:X1], 0, 255).astype(np.uint8))
patch = patch.filter(ImageFilter.GaussianBlur(3))
base[Y0:sky_y1, X0:X1] = np.asarray(patch).astype(np.float64)

alpha_full = np.zeros((H, W))
color_full = np.zeros((H, W, 3))
alpha_full[Y0:Y1, X0:X1] = alpha
color_full[Y0:Y1, X0:X1] = sub      # original glyph colours

# --- 4. shift text layer down by DY ---
a_sh = np.zeros_like(alpha_full)
c_sh = np.zeros_like(color_full)
a_sh[DY:, :] = alpha_full[:-DY, :]
c_sh[DY:, :] = color_full[:-DY, :]

# --- 5. composite moved text onto clean base ---
a3 = a_sh[..., None]
out = base * (1 - a3) + c_sh * a3
out = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(out).save(OUT, quality=95)
print("saved", OUT, "dy", DY)
