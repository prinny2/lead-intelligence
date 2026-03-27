"""
Generate LeadSolar brand images (logo + product cards) using Pillow.
Run: pip install pillow && python generate_images.py
Output: static/logo.png, static/product-starter.png, static/product-pro.png, static/product-empresarial.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path("static")
OUT.mkdir(exist_ok=True)

# ── Brand palette ──────────────────────────────────────────────
BG_DARK   = (6,   12,  24)    # #060c18
BG_CARD   = (13,  24,  37)    # #0d1825
BG_PANEL  = (19,  32,  48)    # #132030
GOLD      = (245, 158, 11)    # #f59e0b
GOLD_DIM  = (180, 115,  8)
WHITE     = (241, 245, 249)   # #f1f5f9
MUTED     = (100, 130, 160)   # #6b85a0
GREEN     = (34,  197,  94)   # #22c55e
BORDER    = (26,  46,  72)    # #1a2e48


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))


def gradient_bg(img, top_color, bot_color):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(h):
        t = y / h
        c = lerp_color(top_color, bot_color, t)
        draw.line([(0, y), (w, y)], fill=c)


def draw_sun(draw, cx, cy, r, color, rays=12):
    """Draw a stylized sun with rays."""
    # Inner glow
    for ring in range(6, 0, -1):
        alpha = int(40 * (ring / 6))
        ring_r = r + ring * 6
        draw.ellipse(
            [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
            fill=(*color[:3],),
            outline=None
        )
    # Rays
    for i in range(rays):
        angle = math.radians(i * (360 / rays))
        x1 = cx + math.cos(angle) * (r + 8)
        y1 = cy + math.sin(angle) * (r + 8)
        x2 = cx + math.cos(angle) * (r + 22)
        y2 = cy + math.sin(angle) * (r + 22)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=3)
    # Core circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    # Inner highlight
    draw.ellipse(
        [cx - r//2, cy - r//2 - 4, cx + r//2 - 4, cy + r//2 - 8],
        fill=(*lerp_color(color, (255, 255, 255), 0.4),)
    )


def load_font(size, bold=False):
    """Try to load a nice font, fall back to default."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def centered_text(draw, text, y, font, color, img_w):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (img_w - tw) // 2
    draw.text((x, y), text, font=font, fill=color)
    return bbox[3] - bbox[1]  # return height


# ── 1. LOGO (400x400, transparent-friendly) ────────────────────
def make_logo():
    W, H = 400, 400
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Dark circle bg
    draw = ImageDraw.Draw(img)
    cx, cy = W//2, H//2
    for ring in range(10, 0, -1):
        r = 190 - ring * 2
        alpha = int(255 * (ring / 10))
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*BG_DARK, alpha))

    # Border ring
    draw.ellipse([cx-185, cy-185, cx+185, cy+185], outline=(*GOLD, 120), width=2)

    # Sun
    draw_sun(draw, cx, cy - 30, 52, GOLD, rays=12)

    # "LS" text inside sun (white)
    f_logo = load_font(28, bold=True)
    bbox = draw.textbbox((0, 0), "LS", font=f_logo)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw//2, cy - 30 - 14), "LS", font=f_logo, fill=(255, 255, 255))

    # "LEADSOLAR" below
    f_name = load_font(30, bold=True)
    bbox = draw.textbbox((0, 0), "LEADSOLAR", font=f_name)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw//2, cy + 36), "LEADSOLAR", font=f_name, fill=WHITE)

    # Tagline
    f_tag = load_font(14)
    bbox = draw.textbbox((0, 0), "Qualificação Solar com IA", font=f_tag)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw//2, cy + 74), "Qualificação Solar com IA", font=f_tag, fill=MUTED)

    # Convert to RGB with white bg for PNG
    bg = Image.new("RGBA", (W, H), (6, 12, 24, 255))
    bg.paste(img, mask=img.split()[3])
    bg = bg.convert("RGB")
    path = OUT / "logo.png"
    bg.save(path, "PNG", optimize=True)
    print(f"✓ {path}")
    return bg


# ── Product card helper ────────────────────────────────────────
def make_product_card(
    filename, plan_name, plan_label, badge_text,
    price_monthly, features, accent=GOLD
):
    W, H = 800, 418
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(H):
        t = y / H
        c = lerp_color(BG_DARK, BG_CARD, t)
        draw.line([(0, y), (W, y)], fill=c)

    # Left panel accent bar
    for x in range(6):
        alpha = 1.0 - x / 6
        c = lerp_color(accent, BG_DARK, 1 - alpha * 0.8)
        draw.line([(x, 0), (x, H)], fill=c)

    # Sun icon top-left
    draw_sun(draw, 72, 72, 30, accent, rays=10)

    # "LS" inside sun
    f_sun = load_font(13, bold=True)
    draw.text((58, 59), "LS", font=f_sun, fill=(255, 255, 255))

    # Brand name
    f_brand = load_font(14)
    draw.text((114, 56), "LeadSolar", font=f_brand, fill=MUTED)

    # Plan badge (top right)
    f_badge = load_font(14, bold=True)
    badge_w = draw.textbbox((0, 0), badge_text, font=f_badge)[2] + 32
    bx = W - badge_w - 30
    draw.rounded_rectangle([bx, 24, bx + badge_w, 56], radius=20,
                            fill=(*accent, 25), outline=(*accent, 80), width=1)
    draw.text((bx + 16, 31), badge_text, font=f_badge, fill=accent)

    # Plan name (big)
    f_plan = load_font(52, bold=True)
    centered_text(draw, plan_name.upper(), 100, f_plan, WHITE, W)

    # Subtitle
    f_sub = load_font(18)
    centered_text(draw, plan_label, 162, f_sub, MUTED, W)

    # Divider
    draw.line([(60, 205), (W - 60, 205)], fill=BORDER, width=1)

    # Features (2 columns)
    f_feat = load_font(15)
    left_x, right_x = 60, W // 2 + 20
    y_start = 222
    dy = 28
    left = features[:len(features)//2 + len(features)%2]
    right = features[len(features)//2 + len(features)%2:]
    for i, feat in enumerate(left):
        draw.text((left_x, y_start + i * dy), "✓ " + feat, font=f_feat, fill=WHITE)
    for i, feat in enumerate(right):
        draw.text((right_x, y_start + i * dy), "✓ " + feat, font=f_feat, fill=WHITE)

    # Bottom strip
    strip_y = H - 52
    for y in range(strip_y, H):
        t = (y - strip_y) / 52
        c = lerp_color(BG_CARD, BG_PANEL, t)
        draw.line([(0, y), (W, y)], fill=c)

    # Price in strip
    f_price_num = load_font(28, bold=True)
    f_price_label = load_font(13)
    price_str = f"R$ {price_monthly}/mês"
    draw.text((left_x, strip_y + 12), price_str, font=f_price_num, fill=accent)
    draw.text((left_x, strip_y + 14), "30 dias grátis • Cancele quando quiser",
              font=f_price_label, fill=MUTED)

    # Trial badge (right side of strip)
    trial_text = "30 dias grátis"
    f_trial = load_font(14, bold=True)
    tw = draw.textbbox((0, 0), trial_text, font=f_trial)[2]
    tx = W - tw - 50
    draw.rounded_rectangle([tx - 12, strip_y + 10, tx + tw + 12, strip_y + 38],
                            radius=12, fill=(*GREEN, 30), outline=(*GREEN, 80), width=1)
    draw.text((tx, strip_y + 14), trial_text, font=f_trial, fill=GREEN)

    path = OUT / filename
    img.save(path, "PNG", optimize=True)
    print(f"✓ {path}")
    return img


# ── 2. STARTER ─────────────────────────────────────────────────
make_product_card(
    "product-starter.png",
    plan_name="Starter",
    plan_label="Ideal para corretores e pequenas equipes",
    badge_text="ATÉ 500 LEADS/MÊS",
    price_monthly="297",
    features=[
        "Score IA 0-10 por lead",
        "Mensagem WhatsApp pronta",
        "Dashboard completo",
        "Export CSV",
        "Até 500 leads/mês",
        "Suporte por email",
    ],
    accent=GOLD,
)

# ── 3. PRO ─────────────────────────────────────────────────────
make_product_card(
    "product-pro.png",
    plan_name="Pro",
    plan_label="Para equipes que escalam vendas solar",
    badge_text="ATÉ 2.000 LEADS/MÊS · MAIS POPULAR",
    price_monthly="497",
    features=[
        "Tudo do Starter",
        "Até 2.000 leads/mês",
        "ROI solar por estado",
        "Upload CSV em lote",
        "Zapier/Make ilimitado",
        "Suporte WhatsApp prioritário",
    ],
    accent=(99, 179, 237),  # blue accent for Pro
)

# ── 4. EMPRESARIAL ─────────────────────────────────────────────
make_product_card(
    "product-empresarial.png",
    plan_name="Empresarial",
    plan_label="Para grandes instaladoras e distribuidoras",
    badge_text="LEADS ILIMITADOS",
    price_monthly="997",
    features=[
        "Tudo do Pro",
        "Leads ilimitados",
        "Onboarding incluso",
        "Treinamento da equipe",
        "SLA 99,9% uptime",
        "Gerente dedicado + NF-e",
    ],
    accent=(168, 85, 247),  # purple accent for Enterprise
)

make_logo()


# ── 5. OG IMAGE (1200x630) ─────────────────────────────────────
def make_og_image():
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(H):
        t = y / H
        c = lerp_color(BG_DARK, BG_CARD, t * 0.8)
        draw.line([(0, y), (W, y)], fill=c)

    # Grid texture
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=(*GOLD, 8) if len(GOLD) == 3 else GOLD)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=(245, 158, 11, 8))

    # Large sun left
    draw_sun(draw, 160, H // 2, 90, GOLD, rays=16)

    # "LS" inside sun
    f_ls = load_font(36, bold=True)
    bbox = draw.textbbox((0, 0), "LS", font=f_ls)
    draw.text((160 - (bbox[2]-bbox[0])//2, H//2 - (bbox[3]-bbox[1])//2), "LS", font=f_ls, fill=WHITE)

    # Tagline above title
    f_tag = load_font(18, bold=True)
    tag_text = "LEADSOLAR  ·  QUALIFICAÇÃO DE LEADS SOLAR COM IA"
    bbox = draw.textbbox((0, 0), tag_text, font=f_tag)
    draw.text((310, 170), tag_text, font=f_tag, fill=GOLD)
    draw.line([(310, 200), (890, 200)], fill=BORDER, width=1)

    # Main headline
    f_h1 = load_font(68, bold=True)
    line1 = "Seu vendedor liga"
    line2 = "pro lead certo."
    draw.text((310, 215), line1, font=f_h1, fill=WHITE)
    draw.text((310, 295), line2, font=f_h1, fill=GOLD)

    # Sub
    f_sub = load_font(24)
    draw.text((310, 390), "Score automático 0–10 · WhatsApp pronto · 30 dias grátis", font=f_sub, fill=MUTED)

    # Pill badges
    f_pill = load_font(16, bold=True)
    pills = ["Starter R$297/mês", "Pro R$497/mês", "Empresarial R$997/mês"]
    px = 310
    for pill in pills:
        bw = draw.textbbox((0, 0), pill, font=f_pill)[2] + 28
        draw.rounded_rectangle([px, 450, px + bw, 486], radius=14, fill=(*BG_PANEL,), outline=(*BORDER,), width=1)
        draw.text((px + 14, 455), pill, font=f_pill, fill=MUTED)
        px += bw + 12

    # Domain
    f_domain = load_font(18)
    draw.text((310, 560), "lead-intelligence-production.up.railway.app", font=f_domain, fill=MUTED)

    path = OUT / "og-image.png"
    img.save(path, "PNG", optimize=True)
    print(f"✓ {path}")


# ── 6. FAVICON (64x64) ────────────────────────────────────────
def make_favicon():
    W = 64
    img = Image.new("RGB", (W, W), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, W], fill=BG_DARK)
    draw_sun(draw, W//2, W//2, 18, GOLD, rays=8)
    f = load_font(11, bold=True)
    bbox = draw.textbbox((0, 0), "LS", font=f)
    draw.text((W//2 - (bbox[2]-bbox[0])//2, W//2 - (bbox[3]-bbox[1])//2 - 1), "LS", font=f, fill=WHITE)
    path = OUT / "favicon.png"
    img.save(path, "PNG", optimize=True)
    # Also 32x32
    img32 = img.resize((32, 32), Image.LANCZOS)
    img32.save(OUT / "favicon-32.png", "PNG", optimize=True)
    print(f"✓ {path}")


make_og_image()
make_favicon()
print("\nTodas as imagens geradas em ./static/")
