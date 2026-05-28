from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageChops, ImageDraw, ImageFont


DPI = 300
W_CM = 70
H_CM = 100
W = round(W_CM / 2.54 * DPI)
H = round(H_CM / 2.54 * DPI)

ROOT = Path(__file__).resolve().parents[1]
POSTER_DIR = ROOT / "poster"
PLOTS = ROOT / "plots"

OUT_PNG = POSTER_DIR / "rootzone_poster_70x100cm.png"
OUT_PDF = POSTER_DIR / "rootzone_poster_70x100cm.pdf"
OUT_PREVIEW = POSTER_DIR / "rootzone_poster_70x100cm_preview.png"

BLUE = "#1976D2"
TEAL = "#006B82"
DARK = "#0D2B38"
DEEP_TEAL = "#006276"
GREEN = "#75C856"
OLIVE = "#A6C946"
LIGHT_BLUE = "#EAF7FB"
PANEL_BLUE = "#F7FDFF"
LIGHT_GREEN = "#F5FCEB"
LIGHT_YELLOW = "#FCFCEB"
BORDER = "#9FD4E8"
TEXT_MUTED = "#4D6C7C"
LINE = "#A8D6E8"
WHITE = "#FFFFFF"


def px(pt):
    return round(pt * DPI / 72)


def font(pt, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(name, px(pt))


F = {
    "title": font(44, True),
    "subtitle": font(22, True),
    "meta": font(18, True),
    "section": font(36, True),
    "h2": font(25, True),
    "body": font(20, False),
    "body_bold": font(20, True),
    "small": font(17, False),
    "small_bold": font(17, True),
    "tiny": font(13, True),
    "metric": font(42, True),
    "metric_small": font(14, True),
    "label": font(20, True),
}


def draw_round(draw, xy, r, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def text_size(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def center_text(draw, xy, text, fnt, fill=DARK, spacing=6):
    x, y, w, h = xy
    lines = text.split("\n")
    heights = []
    widths = []
    for line in lines:
        tw, th = text_size(draw, line, fnt)
        widths.append(tw)
        heights.append(th)
    total_h = sum(heights) + spacing * (len(lines) - 1)
    cy = y + (h - total_h) / 2
    for i, line in enumerate(lines):
        tx = x + (w - widths[i]) / 2
        draw.text((tx, cy), line, font=fnt, fill=fill)
        cy += heights[i] + spacing


def wrap_lines(draw, text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            candidate = line + " " + word
            if text_size(draw, candidate, fnt)[0] <= max_w:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw_wrapped(draw, xy, text, fnt, fill=DARK, leading=1.25):
    x, y, w, _ = xy
    line_h = px(fnt.size * 72 / DPI) if False else round(fnt.size * leading)
    yy = y
    for line in wrap_lines(draw, text, fnt, w):
        draw.text((x, yy), line, font=fnt, fill=fill)
        yy += line_h
    return yy


def fit_paste(base, img, box, mode="contain", bg=None):
    x, y, w, h = [int(v) for v in box]
    src = img.convert("RGBA")
    if mode == "cover":
        scale = max(w / src.width, h / src.height)
        nw, nh = round(src.width * scale), round(src.height * scale)
        src = src.resize((nw, nh), Image.Resampling.LANCZOS)
        left = max(0, (nw - w) // 2)
        top = max(0, (nh - h) // 2)
        src = src.crop((left, top, left + w, top + h))
    else:
        scale = min(w / src.width, h / src.height)
        nw, nh = round(src.width * scale), round(src.height * scale)
        src = src.resize((nw, nh), Image.Resampling.LANCZOS)
        if bg:
            pad = Image.new("RGBA", (w, h), bg)
            pad.alpha_composite(src, ((w - nw) // 2, (h - nh) // 2))
            src = pad
        x += (w - nw) // 2 if not bg else 0
        y += (h - nh) // 2 if not bg else 0
    base.alpha_composite(src, (x, y))


def arrow(draw, start, end, fill=LINE, width=12):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=fill, width=width)
    size = width * 3
    if x2 >= x1:
        pts = [(x2, y2), (x2 - size, y2 - size // 2), (x2 - size, y2 + size // 2)]
    else:
        pts = [(x2, y2), (x2 + size, y2 - size // 2), (x2 + size, y2 + size // 2)]
    draw.polygon(pts, fill=fill)


def load_logos():
    ppt = POSTER_DIR / "hypotheticalocean.pptx"
    with ZipFile(ppt) as z:
        imgs = []
        for name in z.namelist():
            if name.startswith("ppt/media/"):
                data = z.read(name)
                im = Image.open(BytesIO(data)).convert("RGBA")
                imgs.append((name, im))
    ruppin = next(im for name, im in imgs if im.size == (217, 217))
    volcani = next(im for name, im in imgs if im.size == (900, 900))
    return ruppin, volcani


def load_plot(rel):
    img = Image.open(PLOTS / rel).convert("RGBA")
    rgb = img.convert("RGB")
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white"))
    bbox = diff.getbbox()
    if not bbox:
        return img
    pad = 18
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(img.width, bbox[2] + pad)
    bottom = min(img.height, bbox[3] + pad)
    return img.crop((left, top, right, bottom))


def section(draw, x, y, w, h, n, title):
    draw_round(draw, (x, y, x + w, y + h), 80, WHITE, BORDER, 6)
    cx, cy, r = x + 185, y + 205, 135
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=BLUE)
    center_text(draw, (cx - r, cy - r, 2 * r, 2 * r), str(n), font(23, True), WHITE)
    draw.text((x + 360, y + 88), title, font=F["section"], fill=TEAL)
    return x + 155, y + 345, w - 310, h - 435


def mini_metric(draw, x, y, w, h, value, label, accent):
    draw_round(draw, (x, y, x + w, y + h), 38, "#F2FBFE", accent, 4)
    center_text(draw, (x, y + 10, w, h * 0.58), value, F["metric"], accent)
    center_text(draw, (x, y + h * 0.56, w, h * 0.34), label, F["metric_small"], TEXT_MUTED)


def chip(draw, x, y, text, accent=BLUE, fill="#F6FDFF", pad_x=45, h=135):
    w = text_size(draw, text, F["small_bold"])[0] + 2 * pad_x
    draw_round(draw, (x, y, x + w, y + h), 55, fill, accent, 3)
    center_text(draw, (x, y, w, h), text, F["small_bold"], accent)
    return w


def header(base, draw, ruppin, volcani):
    m = 230
    x, y, w, h = m, 170, W - 2 * m, 900
    draw_round(draw, (x, y, x + w, y + h), 90, WHITE, "#4BA5BF", 7)
    fit_paste(base, ruppin, (x + 145, y + 95, 470, 470), "contain")
    fit_paste(base, volcani, (x + w - 615, y + 90, 470, 470), "contain")
    center_text(
        draw,
        (x + 690, y + 80, w - 1380, 360),
        "Predictive Modeling of Rootzone Variables\nUsing Greenhouse Data",
        F["title"],
        TEAL,
        12,
    )
    center_text(
        draw,
        (x + 670, y + 485, w - 1340, 110),
        "Students: Eden Eliyahu, Oren Chaushu",
        F["subtitle"],
        TEAL,
    )
    center_text(
        draw,
        (x + 670, y + 635, w - 1340, 110),
        "Mentors: Dr. Avner Priel - Ruppin,  Dr. Alaa Jamal - Volcani Institute",
        F["meta"],
        DARK,
    )


def section_intro(draw, x, y, w, h):
    cx, cy, cw, ch = section(draw, x, y, w, h, 1, "Introduction & Goal")
    draw.text((cx, cy), "Why rootzone monitoring needs a soft sensor.", font=F["h2"], fill=DARK)
    para = (
        "Rootzone pH and EC are key indicators of nutrient availability, salinity, "
        "and plant health in greenhouse cultivation. Manual samples are accurate, "
        "but they are sparse - between samples, acidity or salinity changes may go undetected."
    )
    draw_wrapped(draw, (cx, cy + 210, cw, 440), para, F["body"], TEXT_MUTED, 1.15)
    box_y = cy + 735
    bh = 790
    bw = (cw - 2 * 190) / 3
    bxs = [cx + i * (bw + 190) for i in range(3)]
    labels = [
        ("Manual\nsample", "accurate -\nsparse", "#006276", "#EFFAFF"),
        ("Blind\ninterval", "no observation", "#78910D", "#FBFEEB"),
        ("Rootzone\nsoft-sensor\nprediction", "dense -\nestimated", BLUE, "#F1F7FF"),
    ]
    for i, (title, sub, col, fill) in enumerate(labels):
        bx = bxs[i]
        draw_round(draw, (bx, box_y, bx + bw, box_y + bh), 90, fill, col, 4)
        draw.ellipse((bx + bw / 2 - 82, box_y + 60, bx + bw / 2 + 82, box_y + 224), outline=col, width=16)
        center_text(draw, (bx + 45, box_y + 280, bw - 90, 260), title, F["label"], col)
        center_text(draw, (bx + 45, box_y + 535, bw - 90, 180), sub, F["small"], TEXT_MUTED)
        if i < 2:
            arrow(draw, (bx + bw + 45, box_y + bh / 2), (bxs[i + 1] - 65, box_y + bh / 2), LINE, 13)
    goal_y = box_y + bh + 120
    draw_round(draw, (cx, goal_y, cx + cw, goal_y + 350), 160, "#F4FCFE", BORDER, 4)
    draw.ellipse((cx + 80, goal_y + 135, cx + 145, goal_y + 200), fill="#A7E08F")
    draw.ellipse((cx + 96, goal_y + 151, cx + 129, goal_y + 184), fill=GREEN)
    draw_wrapped(
        draw,
        (cx + 210, goal_y + 75, cw - 300, 210),
        "Goal - Build a rootzone soft sensor that predicts future pH and EC between manual samples.",
        F["body_bold"],
        TEAL,
        1.15,
    )


def section_dataset(draw, x, y, w, h):
    cx, cy, cw, ch = section(draw, x, y, w, h, 2, "Dataset & Processing")
    draw.text((cx, cy), "Five greenhouse domains synchronized into one 10-minute master dataset.", font=F["h2"], fill=DARK)
    row_x, row_y = cx, cy + 285
    row_w, row_h, gap = int(cw * 0.58), 225, 52
    rows = [
        ("Climate conditions", "temperature - humidity - radiation - ...", BLUE),
        ("Irrigation & fertigation", "volume - fertilizer - acid & salt inputs", GREEN),
        ("Plant status", "canopy cover - crop age - growth stage", OLIVE),
        ("Rootzone measurements", "manual pH samples - manual EC samples", "#08798B"),
        ("Time & history", "timestamps - gaps - previous state - ...", "#1A5570"),
    ]
    for i, (lab, desc, col) in enumerate(rows):
        yy = row_y + i * (row_h + gap)
        draw_round(draw, (row_x, yy, row_x + row_w, yy + row_h), 40, WHITE, BORDER, 3)
        draw.ellipse((row_x + 60, yy + 82, row_x + 118, yy + 140), fill=col)
        draw.text((row_x + 155, yy + 62), lab, font=F["small_bold"], fill=TEAL)
        draw.text((row_x + row_w * 0.50, yy + 67), desc, font=F["small"], fill=TEXT_MUTED)
    card_x = cx + int(cw * 0.63)
    card_y = row_y
    card_w = cw - (card_x - cx)
    card_h = 1330
    draw_round(draw, (card_x, card_y, card_x + card_w, card_y + card_h), 70, DEEP_TEAL, "#034A58", 4)
    center_text(draw, (card_x, card_y + 90, card_w, 320), "MASTER DATASET\n10-minute\ngreenhouse grid", font(20, True), WHITE, 10)
    draw_round(draw, (card_x, card_y + 540, card_x + card_w, card_y + card_h), 40, "#197388", "#197388", 1)
    stats = [("16,682", "ROWS"), ("10 min", "GRAIN"), ("109", "PH LABELS"), ("109", "EC LABELS"), ("20", "COLUMNS"), ("May-Sep", "2025")]
    sx = [card_x + 70, card_x + card_w * 0.52]
    sy = card_y + 625
    for i, (val, lab) in enumerate(stats):
        draw.text((sx[i % 2], sy + (i // 2) * 275), val, font=font(18, True), fill=WHITE)
        draw.text((sx[i % 2], sy + 100 + (i // 2) * 275), lab, font=F["tiny"], fill="#C6EFF7")
    arrow(draw, (row_x + row_w + 40, row_y + 2 * (row_h + gap) + 115), (card_x - 30, card_y + card_h / 2), LINE, 10)
    density_y = card_y + card_h + 90
    draw_round(draw, (cx, density_y, cx + cw, density_y + 535), 45, "#EEF9FC", BORDER, 3)
    draw.text((cx + 90, density_y + 82), "TELEMETRY DENSITY VS. LABEL SPARSITY", font=F["tiny"], fill="#688798")
    draw.text((cx + cw - 1110, density_y + 82), "LABELS: 109 PH - 109 EC", font=F["tiny"], fill=TEAL)
    bar_x, bar_y, bar_w, bar_h = cx + 90, density_y + 190, cw - 180, 78
    draw_round(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), 12, "#BDEAF4", "#90CEDF", 2)
    for i in range(90):
        xx = bar_x + 15 + i * bar_w / 90
        draw.line((xx, bar_y + 12, xx, bar_y + bar_h - 12), fill=DEEP_TEAL, width=8)
    for i in range(30):
        xx = bar_x + 70 + i * (bar_w - 150) / 29
        draw.line((xx, bar_y + bar_h + 34, xx, bar_y + bar_h + 145), fill=BLUE, width=10)
        draw.ellipse((xx - 15, bar_y + bar_h + 25, xx + 15, bar_y + bar_h + 55), fill=BLUE)
    draw.ellipse((cx + 100, density_y + 365, cx + 240, density_y + 505), fill=BLUE)
    center_text(draw, (cx + 100, density_y + 365, 140, 140), "!", font(19, True), WHITE)
    draw.text((cx + 300, density_y + 400), "Main data challenge: dense greenhouse telemetry, sparse rootzone labels.", font=F["small"], fill="#33657C")


def section_architecture(draw, x, y, w, h):
    cx, cy, cw, ch = section(draw, x, y, w, h, 3, "System Architecture & Workflow")
    draw_wrapped(
        draw,
        (cx, cy, cw, 250),
        "Support-signal modeling, rootzone feature engineering, and time-aware development.",
        F["h2"],
        DARK,
        1.15,
    )
    top_y = cy + 300
    box_w, box_h, gap = (cw - 2 * 95) / 3, 420, 95
    top = [
        ("External climate +\nradiation", "temperature - radiation - humidity - ETo", "01"),
        ("Support-signal models", "micro-climate - soil temperature - internal radiation", "02"),
        ("Greenhouse context\nfeatures", "predicted greenhouse context", "03"),
    ]
    for i, (t, s, n) in enumerate(top):
        bx = cx + i * (box_w + gap)
        draw_round(draw, (bx, top_y, bx + box_w, top_y + box_h), 40, WHITE, BORDER, 3)
        draw.text((bx + 55, top_y + 50), t, font=F["small_bold"], fill=TEAL)
        draw_wrapped(draw, (bx + 55, top_y + 190, box_w - 110, 180), s, F["small"], TEXT_MUTED, 1.02)
        draw.text((bx + box_w - 150, top_y + 55), n, font=F["tiny"], fill="#8BBBD0")
        if i < 2:
            arrow(draw, (bx + box_w + 28, top_y + box_h / 2), (bx + box_w + gap - 35, top_y + box_h / 2), LINE, 8)
    input_y = top_y + box_h + 65
    draw_round(draw, (cx, input_y, cx + cw, input_y + 350), 45, "#F3FBEF", GREEN, 3)
    draw.text((cx + 60, input_y + 70), "+ INPUTS", font=F["small_bold"], fill="#3C7A11")
    xx = cx + 360
    for label in ["Irrigation & fertigation", "Crop status", "Rootzone state t0"]:
        ww = chip(draw, xx, input_y + 58, label, "#4A981A", WHITE, 30, 115)
        xx += ww + 45
    chip(draw, cx + 70, input_y + 205, "History", "#4A981A", WHITE, 30, 105)
    draw.text((cx + cw / 2 - 675, input_y + 400), "ROOTZONE FEATURE ENGINEERING", font=F["tiny"], fill=BLUE)
    model_y = input_y + 515
    draw_round(draw, (cx, model_y, cx + cw * 0.72, model_y + 500), 55, DEEP_TEAL, DEEP_TEAL, 1)
    draw.text((cx + 80, model_y + 75), "Rootzone soft sensor", font=font(22, True), fill=WHITE)
    draw_wrapped(
        draw,
        (cx + 80, model_y + 215, cw * 0.68 - 120, 220),
        "predicts pH and EC between manual samples - pH/EC anchor, time gap, irrigation history, fertilizer / salt pressure, crop status",
        F["small_bold"],
        WHITE,
        1.0,
    )
    arrow(draw, (cx + cw * 0.72 + 50, model_y + 250), (cx + cw * 0.78, model_y + 250), DEEP_TEAL, 18)
    out_x = cx + cw * 0.78
    draw_round(draw, (out_x, model_y, cx + cw, model_y + 230), 45, GREEN, GREEN, 1)
    draw_round(draw, (out_x, model_y + 270, cx + cw, model_y + 500), 45, BLUE, BLUE, 1)
    center_text(draw, (out_x, model_y, cx + cw - out_x, 230), "pH(t)", font(19, True), "#06371A")
    center_text(draw, (out_x, model_y + 270, cx + cw - out_x, 230), "EC(t)", font(19, True), WHITE)
    wf_y = y + h - 430
    draw_round(draw, (cx, wf_y, cx + cw, wf_y + 295), 35, "#F7FDFF", BORDER, 3)
    draw.text((cx + 60, wf_y + 90), "PROJECT\nWORKFLOW", font=F["tiny"], fill=TEAL, spacing=12)
    steps = [
        "Problem\nframing", "Data\ncollection", "Audit\n& EDA", "Master\ndataset",
        "Support\nmodeling", "Feature\nengineering", "Model\nbuilding", "Validation", "Deployment"
    ]
    sx = cx + 600
    sw = (cw - 750) / len(steps)
    for i, s in enumerate(steps):
        fill = "#F1FFF1" if i == len(steps) - 1 else WHITE
        outline = GREEN if i == len(steps) - 1 else BORDER
        bx = sx + i * sw
        draw_round(draw, (bx, wf_y + 58, bx + sw - 25, wf_y + 245), 30, fill, outline, 3)
        center_text(draw, (bx, wf_y + 62, sw - 25, 178), f"{i+1:02d}\n{s}", F["tiny"], TEAL, 5)


def section_validation(draw, x, y, w, h):
    cx, cy, cw, ch = section(draw, x, y, w, h, 4, "Model Development & Validation")
    draw_wrapped(draw, (cx, cy, cw, 220), "Trained only on past data, tested on future and skipped samples.", F["h2"], DARK, 1.15)
    y1 = cy + 295
    draw.text((cx, y1), "WALK-FORWARD", font=F["tiny"], fill=TEAL)
    seg_y, seg_h = y1 + 110, 230
    labels = [("Train 1", True), ("Test 1", False), ("Train 2", True), ("Test 2", False), ("Train 3", True), ("Test 3", False), ("Train 4", True), ("Test 4", False)]
    x0 = cx
    unit = (cw - 20 * (len(labels) - 1)) / (4 * 1.55 + 4 * 0.75)
    for lab, train in labels:
        ww = unit * (1.55 if train else 0.75)
        col = "#CFF4FA" if train else BLUE
        txt = TEAL if train else WHITE
        draw_round(draw, (x0, seg_y, x0 + ww, seg_y + seg_h), 35, col, "#8CD4E8", 2)
        center_text(draw, (x0, seg_y, ww, seg_h), lab, F["small_bold"], txt)
        x0 += ww + 20
    y2 = seg_y + 360
    draw.text((cx, y2), "SKIPPED-INTERVAL HOLDOUT", font=F["tiny"], fill=TEAL)
    bar_y, bw, bh = y2 + 110, cw, 225
    draw_round(draw, (cx, bar_y, cx + bw, bar_y + bh), 38, "#DDF7FC", BORDER, 3)
    n = 12
    for i in range(n):
        gap = 28
        sw = (bw - gap * (n + 1)) / n
        xx = cx + gap + i * (sw + gap)
        col = OLIVE if i in [2, 5, 9] else DEEP_TEAL
        draw_round(draw, (xx, bar_y + 45, xx + sw, bar_y + bh - 45), 18, col, col, 1)
    draw.text((cx, bar_y + bh + 90), "Remove labeled intervals and predict them later.", font=F["small"], fill=TEXT_MUTED)
    y3 = bar_y + bh + 285
    draw.text((cx, y3), "BASELINE COMPARISON", font=F["tiny"], fill=TEAL)
    bx_y = y3 + 115
    bx_w = (cw - 80) / 2
    draw_round(draw, (cx, bx_y, cx + bx_w, bx_y + 390), 35, WHITE, BORDER, 3)
    draw.text((cx + 65, bx_y + 80), "Naive carry-forward", font=F["small_bold"], fill=DARK)
    draw.text((cx + 65, bx_y + 205), "Last manual pH / EC", font=F["small"], fill=DARK)
    draw_round(draw, (cx + bx_w + 80, bx_y, cx + cw, bx_y + 390), 35, "#F4FCEB", GREEN, 3)
    draw.text((cx + bx_w + 145, bx_y + 80), "Rootzone soft sensor /", font=F["small_bold"], fill="#1C6C0D")
    draw.text((cx + bx_w + 145, bx_y + 205), "Reduced error vs baseline", font=F["small"], fill="#1C6C0D")
    chips = ["MAE", "RMSE", "R^2", "gain vs naive", "holdout MAE"]
    xx = cx
    for c in chips:
        ww = chip(draw, xx, bx_y + 500, c, TEAL, "#DDF7FC", 40, 135)
        xx += ww + 40


def draw_chart_card(base, draw, x, y, w, h, title, color, metrics, index_img, scatter_img, units):
    draw_round(draw, (x, y, x + w, y + h), 65, "#F8FDFF" if color == TEAL else "#FAFFF5", color, 4)
    draw.ellipse((x + 90, y + 120, x + 205, y + 235), fill=color)
    draw.text((x + 240, y + 82), title, font=font(28, True), fill=color)
    draw.text((x + w - 1120, y + 140), units, font=F["tiny"], fill=TEXT_MUTED)
    mx_y = y + 340
    mx_w = (w - 310) / 3
    for i, (val, lab, accent) in enumerate(metrics):
        mini_metric(draw, x + 90 + i * (mx_w + 65), mx_y, mx_w, 350, val, lab, accent)
    label_y = mx_y + 430
    draw.text((x + 90, label_y), "ACTUAL VS PREDICTED -\nINDEX-BASED", font=F["tiny"], fill=TEXT_MUTED, spacing=8)
    plot1_box = (x + 90, label_y + 175, w - 180, 760)
    draw_round(draw, (plot1_box[0], plot1_box[1], plot1_box[0] + plot1_box[2], plot1_box[1] + plot1_box[3]), 25, WHITE, BORDER, 2)
    fit_paste(base, index_img, (plot1_box[0] + 15, plot1_box[1] + 15, plot1_box[2] - 30, plot1_box[3] - 30), "contain", WHITE)
    label2_y = plot1_box[1] + plot1_box[3] + 70
    draw.text((x + 90, label2_y), "TRUE VS\nPREDICTED", font=F["tiny"], fill=TEXT_MUTED, spacing=8)
    plot2_box = (x + 90, label2_y + 160, w - 180, h - (label2_y + 205 - y))
    draw_round(draw, (plot2_box[0], plot2_box[1], plot2_box[0] + plot2_box[2], plot2_box[1] + plot2_box[3]), 25, WHITE, BORDER, 2)
    fit_paste(base, scatter_img, (plot2_box[0] + 15, plot2_box[1] + 15, plot2_box[2] - 30, plot2_box[3] - 30), "contain", WHITE)


def section_results(base, draw, x, y, w, h):
    cx, cy, cw, ch = section(draw, x, y, w, h, 5, "Results")
    draw_wrapped(draw, (cx, cy, cw, 160), "Rootzone soft sensor - actual vs predicted on walk-forward evaluation.", F["h2"], DARK, 1.08)
    ph_index = load_plot(Path("PH& EC_Results_48H_Version") / "PH" / "ph_actual_vs_pred_index.png")
    ph_scatter = load_plot(Path("PH& EC_Results_48H_Version") / "PH" / "ph_true_vs_pred.png")
    ec_index = load_plot(Path("PH& EC_Results_48H_Version") / "EC" / "ec_actual_vs_pred_index.png")
    ec_scatter = load_plot(Path("PH& EC_Results_48H_Version") / "EC" / "ec_true_vs_pred.png")
    group_gap = 115
    group_w = (cw - group_gap) / 2
    groups = [
        (cx, "pH", "PH UNITS - N = 56", TEAL, "#F8FDFF", [("0.330", "MAE", TEAL), ("0.932", "R^2", TEAL), ("62.4%", "GAIN VS\nNAIVE", BLUE)]),
        (cx + group_w + group_gap, "EC", "MS/CM - N = 56", GREEN, "#FAFFF5", [("0.127", "MAE", "#1F5D17"), ("0.982", "R^2", "#1F5D17"), ("35.3%", "GAIN VS\nNAIVE", BLUE)]),
    ]
    metric_y = cy + 265
    metric_h = 575
    for gx, title, units, col, fill, metrics in groups:
        draw_round(draw, (gx, metric_y, gx + group_w, metric_y + metric_h), 55, fill, col, 4)
        draw.ellipse((gx + 95, metric_y + 85, gx + 215, metric_y + 205), fill=col)
        draw.text((gx + 255, metric_y + 72), title, font=font(32, True), fill=col)
        draw.text((gx + group_w - 1140, metric_y + 115), units, font=F["tiny"], fill=TEXT_MUTED)
        mx_w = (group_w - 320) / 3
        for i, (val, lab, accent) in enumerate(metrics):
            mini_metric(draw, gx + 95 + i * (mx_w + 65), metric_y + 250, mx_w, 255, val, lab, accent)

    def plot_box(label, img, gx, yy, hh, outline):
        draw.text((gx, yy - 70), label, font=F["tiny"], fill=TEXT_MUTED)
        draw_round(draw, (gx, yy, gx + group_w, yy + hh), 30, WHITE, outline, 3)
        fit_paste(base, img, (gx + 30, yy + 30, group_w - 60, hh - 60), "contain", WHITE)

    line_y = metric_y + metric_h + 175
    line_h = 880
    scatter_y = line_y + line_h + 205
    scatter_h = ch - (scatter_y - cy) - 85
    ph_x = groups[0][0]
    ec_x = groups[1][0]
    plot_box("ACTUAL VS PREDICTED - INDEX-BASED", ph_index, ph_x, line_y, line_h, TEAL)
    plot_box("ACTUAL VS PREDICTED - INDEX-BASED", ec_index, ec_x, line_y, line_h, GREEN)
    plot_box("TRUE VS PREDICTED", ph_scatter, ph_x, scatter_y, scatter_h, TEAL)
    plot_box("TRUE VS PREDICTED", ec_scatter, ec_x, scatter_y, scatter_h, GREEN)


def section_impact(draw, x, y, w, h):
    cx, cy, cw, ch = section(draw, x, y, w, h, 6, "Conclusions & Impact")
    draw_wrapped(draw, (cx, cy, cw, 150), "Sparse manual samples are now a usable 10-minute prediction workflow for monitoring and decisions.", F["h2"], DARK, 1.05)
    call_y = cy + 135
    draw_round(draw, (cx, call_y, cx + cw, call_y + 150), 38, "#EAFBFF", "#EAFBFF", 1)
    draw.rectangle((cx, call_y, cx + 28, call_y + 150), fill=TEAL)
    draw_wrapped(
        draw,
        (cx + 80, call_y + 38, cw - 130, 90),
        "Helps growers monitor rootzone conditions continuously and respond earlier to salinity or acidity changes between manual samples.",
        F["body"],
        TEAL,
        1.05,
    )
    box_y = call_y + 205
    impacts = [
        ("Earlier awareness", "Predicts movement between manual samples.", GREEN, "#F4FCEA"),
        ("Decision support", "Supports fertigation, irrigation, and acid dosing.", BLUE, "#EDF5FF"),
        ("Usable workflow", "Packaged as ETL, prediction, and dashboard workflow.", OLIVE, "#FCFCEB"),
    ]
    box_gap = 90
    box_w = (cw - 2 * box_gap) / 3
    for title, desc, col, fill in impacts:
        bx = cx + impacts.index((title, desc, col, fill)) * (box_w + box_gap)
        draw_round(draw, (bx, box_y, bx + box_w, box_y + 255), 44, fill, col, 4)
        draw.ellipse((bx + 55, box_y + 58, bx + 155, box_y + 158), fill=col)
        center_text(draw, (bx + 55, box_y + 58, 100, 100), "i", font(15, True), WHITE)
        draw.text((bx + 190, box_y + 48), title, font=F["label"], fill="#1B4120")
        draw_wrapped(draw, (bx + 190, box_y + 145, box_w - 235, 85), desc, F["small"], TEXT_MUTED, 0.96)


def main():
    POSTER_DIR.mkdir(exist_ok=True)
    base = Image.new("RGBA", (W, H), "#DCE9EF")
    draw = ImageDraw.Draw(base)
    draw.rectangle((125, 125, W - 125, H - 125), fill=WHITE)
    ruppin, volcani = load_logos()
    header(base, draw, ruppin, volcani)

    margin = 230
    gap = 120
    y1 = 1180
    row1_h = 2600
    row2_y = 3920
    row2_h = 2600
    row3_y = 6660
    row3_h = 3850
    row4_y = 10650
    row4_h = 1030

    top_w1 = 3300
    top_w2 = W - 2 * margin - gap - top_w1
    section_intro(draw, margin, y1, top_w1, row1_h)
    section_dataset(draw, margin + top_w1 + gap, y1, top_w2, row1_h)

    col_w = (W - 2 * margin - gap) / 2
    section_architecture(draw, margin, row2_y, col_w, row2_h)
    section_validation(draw, margin + col_w + gap, row2_y, col_w, row2_h)

    full_w = W - 2 * margin
    section_results(base, draw, margin, row3_y, full_w, row3_h)
    section_impact(draw, margin, row4_y, full_w, row4_h)

    rgb = base.convert("RGB")
    rgb.save(OUT_PNG, dpi=(DPI, DPI), optimize=True)
    rgb.save(OUT_PDF, "PDF", resolution=DPI)
    preview = rgb.copy()
    preview.thumbnail((2200, 3200), Image.Resampling.LANCZOS)
    preview.save(OUT_PREVIEW)
    print(OUT_PNG)
    print(OUT_PDF)
    print(OUT_PREVIEW)
    print(f"{W}x{H}px at {DPI} DPI = {W_CM}x{H_CM} cm")


if __name__ == "__main__":
    main()
