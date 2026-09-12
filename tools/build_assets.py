"""Turn the WhatsApp logo JPEG into web assets: transparent PNG, icons, OG card."""
import os
from collections import deque
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Users\onyan\Downloads\WhatsApp Image 2026-09-12 at 18.53.59.jpeg"
OUT = r"C:\Users\onyan\.vscode\InvoiceRUS\assets"
os.makedirs(OUT, exist_ok=True)

INK = (15, 35, 64)
INK_SOFT = (66, 86, 111)
ACCENT = (51, 64, 181)

# ---------- 1. background -> transparent via edge flood fill ----------
im = Image.open(SRC).convert("RGBA")
w, h = im.size
px = im.load()

THRESH = 238  # anything this light, reachable from the border, is background


def is_bg(p):
    r, g, b, _ = p
    return r >= THRESH and g >= THRESH and b >= THRESH


seen = bytearray(w * h)
q = deque()
for x in range(w):
    for y in (0, h - 1):
        if is_bg(px[x, y]) and not seen[y * w + x]:
            seen[y * w + x] = 1
            q.append((x, y))
for y in range(h):
    for x in (0, w - 1):
        if is_bg(px[x, y]) and not seen[y * w + x]:
            seen[y * w + x] = 1
            q.append((x, y))

while q:
    x, y = q.popleft()
    px[x, y] = (255, 255, 255, 0)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and is_bg(px[nx, ny]):
            seen[ny * w + nx] = 1
            q.append((nx, ny))

im = im.crop(im.getbbox())
print("trimmed to", im.size)

# upscale once with a good filter so retina headers stay crisp
big = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
big.save(os.path.join(OUT, "octopus.png"))


def square(img, size, pad_ratio=0.0):
    """Fit img into a transparent square canvas of `size`."""
    inner = int(size * (1 - pad_ratio * 2))
    c = img.copy()
    c.thumbnail((inner, inner), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    canvas.paste(c, ((size - c.width) // 2, (size - c.height) // 2), c)
    return canvas


square(big, 512).save(os.path.join(OUT, "icon-512.png"))
square(big, 192).save(os.path.join(OUT, "icon-192.png"))
square(big, 32).save(os.path.join(OUT, "favicon-32.png"))

# apple touch icons are composited on white by iOS anyway - bake it in
apple = Image.new("RGBA", (180, 180), (255, 255, 255, 255))
t = square(big, 180, pad_ratio=0.07)
apple.paste(t, (0, 0), t)
apple.convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"))

# multi-resolution .ico for maximum browser coverage
square(big, 256).save(
    os.path.join(OUT, "favicon.ico"),
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
)


# ---------- 2. Open Graph card ----------
def font(names, size):
    for n in names:
        p = os.path.join(r"C:\Windows\Fonts", n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


f_display = font(["georgiab.ttf", "georgia.ttf", "times.ttf"], 76)
f_body = font(["segoeui.ttf", "arial.ttf"], 30)
f_mono = font(["consola.ttf", "cour.ttf"], 23)

og = Image.new("RGB", (1200, 630), (255, 255, 255))
d = ImageDraw.Draw(og)

logo = big.copy()
logo.thumbnail((190, 190), Image.LANCZOS)
og.paste(logo, (84, 74), logo)

d.text((300, 116), "OCTOPUS", font=font(["consolab.ttf", "consola.ttf"], 30),
       fill=ACCENT)
d.text((300, 158), "Accounts receivable teammate",
       font=font(["segoeui.ttf", "arial.ttf"], 27), fill=INK_SOFT)

d.text((84, 312), "Every invoice", font=f_display, fill=INK)
d.text((84, 398), "gets an owner.", font=f_display, fill=INK)

d.line([(84, 520), (1116, 520)], fill=(225, 231, 240), width=2)
d.text((84, 548), "For outsourced accounting & AR firms  ·  Design partner program",
       font=f_mono, fill=INK_SOFT)

og.save(os.path.join(OUT, "og-card.png"))

print("wrote:", sorted(os.listdir(OUT)))
