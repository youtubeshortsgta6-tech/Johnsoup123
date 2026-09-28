"""Original graphic cards for VICE Check: dark background, hot-pink / teal accents, "VI" badge top-right.

Usage (library):  from cards import Card; Card().title("...", "...").save(path)
Usage (cli):      python cards.py work/cards    -> renders every card the Florida shotlist names
All art is drawn here from primitives. No logos, no game art, no faces.
"""
import sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
BG = (11, 12, 20)
BG2 = (18, 20, 34)
PINK = (255, 45, 149)
TEAL = (25, 227, 209)
WHITE = (245, 245, 250)
GREY = (150, 155, 175)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def font(size, bold=True):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    except OSError:
        return ImageFont.load_default(size=size)

class Card:
    def __init__(self, w=W, h=H):
        self.im = Image.new("RGB", (w, h), BG)
        self.d = ImageDraw.Draw(self.im)
        self._backdrop()
        self._badge()

    # -- chrome -------------------------------------------------------------
    def _backdrop(self):
        w, h = self.im.size
        glow = Image.new("RGB", (w, h), BG)
        g = ImageDraw.Draw(glow)
        g.ellipse([-w*0.25, h*0.55, w*0.35, h*1.35], fill=(60, 10, 40))
        g.ellipse([w*0.7, -h*0.4, w*1.3, h*0.35], fill=(8, 55, 60))
        glow = glow.filter(ImageFilter.GaussianBlur(160))
        self.im.paste(glow)
        self.d = ImageDraw.Draw(self.im)
        # subtle grid
        for x in range(0, w, 96):
            self.d.line([(x, 0), (x, h)], fill=(20, 22, 36), width=1)
        for y in range(0, h, 96):
            self.d.line([(0, y), (w, y)], fill=(20, 22, 36), width=1)
        self.d.rectangle([0, h-10, w, h], fill=PINK)
        self.d.rectangle([0, h-10, int(w*0.38), h], fill=TEAL)

    def _badge(self):
        w, _ = self.im.size
        x1, y1, x2, y2 = w-190, 44, w-50, 128
        self.d.rounded_rectangle([x1, y1, x2, y2], radius=16, outline=PINK, width=5, fill=BG2)
        f = font(56)
        self.d.text(((x1+x2)//2, (y1+y2)//2), "VI", font=f, fill=WHITE, anchor="mm")
        self.d.text((w-52, 140), "VICE CHECK", font=font(20), fill=TEAL, anchor="ra")

    def _wrap(self, text, f, maxw):
        words, lines, cur = text.split(), [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if self.d.textlength(t, font=f) <= maxw: cur = t
            else: lines.append(cur); cur = wd
        if cur: lines.append(cur)
        return lines

    def _block(self, text, f, x, y, maxw, fill=WHITE, gap=14, anchor="la"):
        for line in self._wrap(text, f, maxw):
            self.d.text((x, y), line, font=f, fill=fill, anchor=anchor)
            y += f.size + gap
        return y

    # -- card types -----------------------------------------------------------
    def title(self, kicker, title, sub=None):
        self.d.text((120, 300), kicker.upper(), font=font(44), fill=TEAL)
        y = self._block(title, font(112), 120, 370, 1500)
        if sub: self._block(sub, font(40, False), 120, y+20, 1500, fill=GREY)
        return self

    def chapter(self, number, name, subtitle=None):
        self.d.text((120, 380), f"STOP {number}" if number else "", font=font(60), fill=PINK)
        self._block(name, font(140), 120, 450, 1600)
        if subtitle: self._block(subtitle, font(44, False), 120, 640, 1600, fill=GREY)
        return self

    def quote(self, text, source):
        self.d.text((120, 260), "“", font=font(220), fill=PINK)
        y = self._block(text, font(72, False), 220, 330, 1450)
        self.d.text((220, y+30), f"— {source}", font=font(40), fill=TEAL)
        return self

    def facts(self, heading, items):
        self.d.text((120, 200), heading, font=font(80), fill=WHITE)
        y = 340
        for it in items:
            self.d.rectangle([120, y+14, 140, y+54], fill=PINK)
            y = self._block(it, font(56, False), 170, y, 1500, gap=10) + 22
        return self

    def compare(self, left_label, left_text, right_label, right_text, left_img=None, right_img=None):
        """Side-by-side. Images (paths) are owner-supplied; missing ones show a labelled panel."""
        pad, top, bottom = 80, 200, 940
        mid = W // 2
        for (x1, x2, label, text, img, color) in [
            (pad, mid-30, left_label, left_text, left_img, TEAL),
            (mid+30, W-pad, right_label, right_text, right_img, PINK)]:
            self.d.rounded_rectangle([x1, top, x2, bottom], radius=24, fill=BG2, outline=color, width=4)
            if img and Path(img).exists():
                pic = Image.open(img).convert("RGB")
                bw, bh = x2-x1-24, bottom-top-160
                pic.thumbnail((bw, bh))
                self.im.paste(pic, (x1+12+(bw-pic.width)//2, top+12+(bh-pic.height)//2))
            else:
                self.d.text(((x1+x2)//2, (top+bottom)//2-60), "IMAGE", font=font(40), fill=(60, 64, 90), anchor="mm")
            self.d.text((x1+30, top+24), label.upper(), font=font(30), fill=color)
            self._block(text, font(52), x1+30, bottom-130, x2-x1-60)
        return self

    def leonida_map(self, labels, highlight=None, scoreboard=None):
        """Original schematic outline of a fictional peninsula with region labels. Positions are approximate by design."""
        # abstract peninsula polygon (original, not a traced map)
        pts = [(700, 120), (1050, 110), (1180, 200), (1200, 330), (1150, 470), (1190, 600),
               (1180, 760), (1130, 880), (1020, 960), (930, 990), (880, 940), (900, 830),
               (860, 700), (800, 560), (720, 420), (650, 300), (640, 190)]
        shadow = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).polygon(pts, fill=(25, 227, 209, 60))
        shadow = shadow.filter(ImageFilter.GaussianBlur(30))
        self.im.paste(shadow, (0, 0), shadow)
        self.d = ImageDraw.Draw(self.im)
        self.d.polygon(pts, fill=(16, 40, 48), outline=TEAL)
        self.d.line(pts + [pts[0]], fill=TEAL, width=6, joint="curve")
        # lake
        self.d.ellipse([930, 470, 1060, 570], fill=(10, 20, 30), outline=TEAL, width=3)
        # keys: dots trailing south-west
        for i in range(6):
            self.d.ellipse([880-i*38, 985+i*10, 900-i*38, 1000+i*10], fill=(16, 40, 48), outline=TEAL, width=2)
        f = font(40); fs = font(30, False)
        for name, (x, y), real in labels:
            on = highlight is None or name in highlight
            col = PINK if on else GREY
            self.d.ellipse([x-10, y-10, x+10, y+10], fill=col)
            self.d.text((x+22, y-24), name, font=f, fill=WHITE if on else GREY)
            if scoreboard and real:
                self.d.text((x+22, y+20), real, font=fs, fill=col)
        self.d.text((120, 200), "LEONIDA", font=font(90), fill=WHITE)
        self.d.text((120, 300), "SIX OFFICIAL REGIONS" if not scoreboard else "THE SCOREBOARD", font=font(40), fill=TEAL)
        self.d.text((120, 980), "Schematic. Approximate positions.", font=font(28, False), fill=GREY)
        return self

    def placeholder(self, what, file=None):
        self.d.rectangle([0, 0, W, H], fill=(40, 12, 12))
        self._badge()
        self.d.text((120, 300), "MISSING FOOTAGE", font=font(80), fill=PINK)
        y = self._block(what, font(48, False), 120, 420, 1600)
        if file: self._block(f"expected file: {file}", font(36, False), 120, y+30, 1600, fill=GREY)
        return self

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.im.save(path, "PNG")
        return path

REGIONS = [("Mount Kalaga", (760, 200), "no clean match"),
           ("Port Gellhorn", (690, 420), "Panama City"),
           ("Ambrosia", (1075, 520), "Clewiston"),
           ("Grassrivers", (890, 720), "the Everglades"),
           ("Vice City", (1140, 800), "Miami"),
           ("Leonida Keys", (760, 1000), "the Florida Keys")]

if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("work/cards")
    Card().title("VICE Check", "Every Real Florida Location Hidden in GTA 6").save(out/"title.png")
    Card().leonida_map(REGIONS).save(out/"map.png")
    Card().leonida_map(REGIONS, scoreboard=True).save(out/"scoreboard.png")
    Card().leonida_map(REGIONS, highlight=["Ambrosia"]).save(out/"map-lake.png")
    Card().quote("The dress code is casual, the bars are loaded.", "Rockstar, on the Leonida Keys").save(out/"quote-keys.png")
    Card().facts("Betsy the Lobster", ["30 feet tall, 40 feet long", "Finished in 1985, Islamorada", "Second most photographed spot in the Keys"]).save(out/"facts-betsy.png")
    Card().facts("Rockstar's method", ["Take a real place", "Change one detail", "Call it somewhere else"]).save(out/"method.png")
    Card().facts("The Everglades", ["Everglades National Park: about 1.5 million acres", "Vice City (2002) never left the city limits", "GTA 6 builds a whole swamp region"]).save(out/"facts-everglades.png")
    Card().facts("Lake Okeechobee", ["Biggest freshwater lake in Florida", "About 730 square miles", "Clewiston on the southwest shore: America's Sweetest Town"]).save(out/"facts-okeechobee.png")
    Card().quote("The refinery provides the jobs, and the local biker gang provides almost everything else.", "Rockstar, on Ambrosia").save(out/"quote-ambrosia.png")
    Card().facts("Ambrosia", ["Allied Crystal sugar refinery", "Allied Crystal branding on election signs", "Ambrosia: food of the gods, impossibly sweet"]).save(out/"facts-ambrosia.png")
    Card().quote("The new economy here is fueled by malt liquor, painkillers, and truck stop energy drinks.", "Rockstar, on Port Gellhorn").save(out/"quote-gellhorn.png")
    Card().facts("Port Gellhorn = Panama City?", ["Panama City Beach: spring break capital until the 2015 crackdown", "Martha Gellhorn, war correspondent, covered the 1989 Panama invasion", "Fan theory. Rockstar hasn't confirmed it"]).save(out/"facts-gellhorn.png")
    Card().quote("Hillbilly mystics and paranoid radicals, living far from the prying eyes of the government.", "Rockstar, on Mount Kalaga").save(out/"quote-kalaga.png")
    Card().facts("Florida has no mountains", ["Highest natural point: Britton Hill, 345 ft", "Closest thing: Torreya State Park bluffs, Apalachicola River", "Mount Kalaga is Rockstar's invention"]).save(out/"facts-kalaga.png")
    Card().title("Your turn", "What inspired Mount Kalaga?", "Drop your theory in the comments").save(out/"question.png")
    Card().facts("Florida, through Rockstar's filter", ["A lobster becomes a whale", "A sugar town gets a biker gang", "A war reporter's name becomes a city"]).save(out/"filter.png")
    Card().title("Next week", "GTA 6 vs GTA 5, frame by frame", "Subscribe so you catch it. Daily updates: GTA6 Shorts, linked below").save(out/"endscreen.png")
    print("cards ->", out)
