"""1280x720 thumbnail.
  --image <official screenshot> --text "LINE|LINE|LINE" [--sub ...] [--focus fx,fy] [--split <real photo> --split-focus fx,fy]
  --text only: legacy dark text card.   no flags: legacy primitive lobster/whale card.
"""
import math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from cards import font, PINK, TEAL, WHITE, BG2

def sky(w, h, top, bottom):
    col = Image.new("RGB", (1, h))
    px = col.load()
    for y in range(h):
        t = y / h
        px[0, y] = tuple(int(top[i]*(1-t) + bottom[i]*t) for i in range(3))
    return col.resize((w, h))

def lobster(d, ox, oy, s, col=(214, 40, 40)):
    # body, tail segments, claws, antennae: simple shapes only
    d.ellipse([ox, oy, ox+s*1.6, oy+s*0.8], fill=col)
    for i in range(4):
        d.ellipse([ox+s*1.3+i*s*0.28, oy+s*0.15+i*s*0.05, ox+s*1.7+i*s*0.28, oy+s*0.65+i*s*0.05], fill=col)
    d.polygon([(ox+s*2.5, oy+s*0.4), (ox+s*2.9, oy+s*0.15), (ox+s*2.9, oy+s*0.75)], fill=col)
    d.ellipse([ox-s*0.55, oy-s*0.15, ox+s*0.25, oy+s*0.45], fill=col)      # claw
    d.ellipse([ox-s*0.5, oy+s*0.45, ox+s*0.3, oy+s*1.0], fill=col)
    d.line([(ox+s*0.2, oy+s*0.1), (ox-s*0.6, oy-s*0.7)], fill=col, width=int(s*0.06))
    d.line([(ox+s*0.4, oy+s*0.1), (ox-s*0.2, oy-s*0.8)], fill=col, width=int(s*0.06))
    d.ellipse([ox+s*0.25, oy+s*0.2, ox+s*0.38, oy+s*0.33], fill=WHITE)

def whale(d, ox, oy, s, col=(40, 90, 200)):
    # big rounded body, tapering tail, fluke, belly stripe, spout: simple shapes only
    d.rounded_rectangle([ox, oy, ox+s*2.2, oy+s*1.1], radius=int(s*0.55), fill=col)
    d.polygon([(ox+s*1.9, oy+s*0.25), (ox+s*2.8, oy+s*0.45), (ox+s*2.8, oy+s*0.65), (ox+s*1.9, oy+s*0.95)], fill=col)
    d.polygon([(ox+s*2.7, oy+s*0.55), (ox+s*3.1, oy+s*0.15), (ox+s*3.2, oy+s*0.45), (ox+s*3.2, oy+s*0.65), (ox+s*3.1, oy+s*0.95)], fill=col)
    d.polygon([(ox+s*0.9, oy+s*1.0), (ox+s*1.2, oy+s*1.35), (ox+s*1.5, oy+s*1.0)], fill=col)   # flipper
    d.chord([ox+s*0.15, oy+s*0.7, ox+s*1.9, oy+s*1.35], 0, 180, fill=(120, 170, 235))      # belly
    d.ellipse([ox+s*0.35, oy+s*0.3, ox+s*0.5, oy+s*0.45], fill=WHITE)
    d.ellipse([ox+s*0.39, oy+s*0.34, ox+s*0.46, oy+s*0.41], fill=(10, 10, 30))
    for k in (-1, 0, 1):
        d.line([(ox+s*0.75, oy-s*0.05), (ox+s*0.75+k*s*0.35, oy-s*0.5)], fill=(160, 220, 255), width=int(s*0.07))

def pedestal(d, cx, y, w, col=(70, 70, 80)):
    d.rectangle([cx-w//2, y, cx+w//2, y+40], fill=col)
    d.rectangle([cx-w//2-30, y+40, cx+w//2+30, y+70], fill=(50, 50, 60))

def palm(d, x, y, h, col=(20, 90, 60)):
    d.line([(x, y), (x+10, y-h)], fill=(90, 60, 30), width=14)
    for ang in (-60, -30, 0, 30, 60):
        ex = x+10 + math.cos(math.radians(ang-90))*h*0.45
        ey = y-h + math.sin(math.radians(ang-90))*h*0.45 + h*0.1
        d.line([(x+10, y-h), (ex, ey)], fill=col, width=18)

def build(path):
    W, H = 1280, 720
    im = Image.new("RGB", (W, H), BG2)
    left = sky(W//2, H, (120, 200, 255), (255, 235, 160))
    right = sky(W//2, H, (40, 10, 70), (255, 80, 160))
    im.paste(left, (0, 0)); im.paste(right, (W//2, 0))
    d = ImageDraw.Draw(im)
    for x0, ground in ((0, (215, 190, 120)), (W//2, (90, 30, 90))):
        d.rectangle([x0, 540, x0+W//2, H], fill=ground)
    palm(d, 60, 560, 260); palm(d, 560, 560, 200); palm(d, 700, 560, 220); palm(d, 1200, 560, 260, (30, 20, 60))
    pedestal(d, 320, 470, 300); pedestal(d, 960, 470, 300)
    lobster(d, 200, 250, 110)
    whale(d, 760, 230, 110)
    # arrow
    d.line([(560, 360), (760, 360)], fill=(230, 30, 30), width=26)
    d.polygon([(740, 320), (800, 360), (740, 400)], fill=(230, 30, 30))
    d.line([(560, 360), (760, 360)], fill=WHITE, width=6)
    # REAL? text with outline
    f = font(150)
    for dx in (-6, 6):
        for dy in (-6, 6):
            d.text((W-60+dx, H-40+dy), "REAL?", font=f, fill=(0, 0, 0), anchor="rd")
    d.text((W-60, H-40), "REAL?", font=f, fill=WHITE, anchor="rd")
    # VI badge
    d.rounded_rectangle([30, 30, 170, 120], radius=16, outline=PINK, width=6, fill=BG2)
    d.text((100, 75), "VI", font=font(60), fill=WHITE, anchor="mm")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG")
    return path

def build_text(path, headline, sub=None):
    """Generic VICE Check thumbnail: dark pink/teal backdrop, huge headline, optional sub line, VI badge."""
    from cards import Card, font, GREY
    c = Card(1280, 720)
    c.d.rectangle([0, 0, 1280, 720], fill=(11, 12, 20))
    c._backdrop(); c._badge()
    lines = headline.upper().split("|")
    y = 110 if len(lines) >= 3 else 170
    for i, line in enumerate(lines):
        f = font((136 if len(lines) >= 3 else 150) if len(line) <= 9 else 112 if len(line) <= 13 else 90)
        for dx in (-5, 5):
            for dy in (-5, 5):
                c.d.text((60+dx, y+dy), line, font=f, fill=(0, 0, 0))
        c.d.text((60, y), line, font=f, fill=WHITE if i % 2 == 0 else PINK)
        y += f.size + 10
    if sub:
        c.d.text((64, 692), sub, font=font(38, False), fill=TEAL, anchor="ld")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    c.im.save(path, "PNG")
    return path

def _cover(img, w, h, focus=None):
    """Scale-and-crop an image to w x h. focus=(fx, fy) in 0..1 picks which part survives the crop."""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    img = img.resize((int(iw * scale + 0.5), int(ih * scale + 0.5)), Image.LANCZOS)
    fx, fy = focus or (0.5, 0.5)
    x0 = int((img.width - w) * fx); y0 = int((img.height - h) * fy)
    return img.crop((x0, y0, x0 + w, y0 + h))

def _pop(img):
    from PIL import ImageEnhance
    img = ImageEnhance.Color(img).enhance(1.25)
    return ImageEnhance.Contrast(img).enhance(1.12)

def _outlined(d, xy, text, f, fill, outline=(0, 0, 0), w=7, anchor="la"):
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
            d.text((xy[0] + dx, xy[1] + dy), text, font=f, fill=outline, anchor=anchor)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)

def _badge_big(d, W):
    d.rounded_rectangle([W - 200, 36, W - 40, 136], radius=18, outline=PINK, width=6, fill=BG2)
    d.text((W - 120, 86), "VI", font=font(66), fill=WHITE, anchor="mm")
    _outlined(d, (W - 40, 150), "VICE CHECK", font(24), TEAL, w=3, anchor="ra")

def build_image(path, headline, sub, image, focus=None, split=None, mirror=False):
    """Full-bleed official screenshot, dark left gradient, huge outlined hook text, VI badge.
    split=(right_image, right_focus) makes a GTA-vs-real split frame with the headline centred at the bottom."""
    W, H = 1280, 720
    if split:
        left = _pop(_cover(Image.open(image).convert("RGB"), W // 2, H, focus))
        right = _pop(_cover(Image.open(split[0]).convert("RGB"), W // 2, H, split[1]))
        im = Image.new("RGB", (W, H)); im.paste(left, (0, 0)); im.paste(right, (W // 2, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([W // 2 - 6, 0, W // 2 + 6, H], fill=WHITE)
        # bottom gradient for the text
        grad = Image.new("L", (1, H)); gp = grad.load()
        for y in range(H): gp[0, y] = int(max(0, (y - 380) / (H - 380)) ** 1.2 * 235)
        im.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), grad.resize((W, H)))
        d = ImageDraw.Draw(im)
        _outlined(d, (30, 30), "GTA 6", font(48), WHITE, w=4)
        _outlined(d, (W // 2 + 30, 30), "REAL", font(48), PINK, w=4)
        lines = headline.upper().split("|")
        y = H - 40
        for i, line in enumerate(reversed(lines)):
            f = font(150 if len(line) <= 7 else 120 if len(line) <= 11 else 96)
            _outlined(d, (W // 2, y), line, f, PINK if i == 0 else WHITE, w=8, anchor="md")
            y -= f.size + 6
        _badge_big(d, W)
    else:
        im = _pop(_cover(Image.open(image).convert("RGB"), W, H, focus))
        if mirror: im = im.transpose(Image.FLIP_LEFT_RIGHT)   # puts a left-side subject on the right, clear of the text
        grad = Image.new("L", (W, 1)); gp = grad.load()
        for x in range(W):
            t = x / W
            gp[x, 0] = int(max(0.0, 1 - (t / 0.72)) ** 0.9 * 215) if t < 0.72 else 0
        im.paste(Image.new("RGB", (W, H), (4, 3, 10)), (0, 0), grad.resize((W, H)))
        d = ImageDraw.Draw(im)
        lines = headline.upper().split("|")
        sizes = [150 if len(l) <= 7 else 128 if len(l) <= 10 else 104 if len(l) <= 13 else 84 for l in lines]
        total = sum(sizes) + 8 * (len(lines) - 1)
        y = (H - total) // 2 - 10
        for i, (line, sz) in enumerate(zip(lines, sizes)):
            _outlined(d, (56, y), line, font(sz), WHITE if i % 2 == 0 else PINK, w=8)
            y += sz + 8
        if sub:
            _outlined(d, (60, H - 28), sub, font(40, False), TEAL, w=4, anchor="ld")
        d.rectangle([0, H - 10, W, H], fill=PINK)
        _badge_big(d, W)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG")
    return path

if __name__ == "__main__":
    if "--image" in sys.argv:
        a = sys.argv
        head = a[a.index("--text") + 1]
        sub = a[a.index("--sub") + 1] if "--sub" in a else None
        focus = tuple(float(v) for v in a[a.index("--focus") + 1].split(",")) if "--focus" in a else None
        split = None
        if "--split" in a:
            split = (a[a.index("--split") + 1], tuple(float(v) for v in a[a.index("--split-focus") + 1].split(",")) if "--split-focus" in a else None)
        print(build_image(a[1], head, sub, a[a.index("--image") + 1], focus, split, "--mirror" in a)); sys.exit()
    if "--text" in sys.argv:
        head = sys.argv[sys.argv.index("--text") + 1]
        sub = sys.argv[sys.argv.index("--sub") + 1] if "--sub" in sys.argv else None
        print(build_text(sys.argv[1], head, sub)); sys.exit()
    print(build(sys.argv[1] if len(sys.argv) > 1 else "out/thumb-test.png"))
