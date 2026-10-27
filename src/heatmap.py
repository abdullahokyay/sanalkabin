import numpy as np
from PIL import Image, ImageDraw, ImageFilter

COLORS = {
    "red": (230, 40, 40),
    "orange": (245, 150, 30),
    "green": (40, 190, 90),
    "blue": (50, 120, 235),
}

EMOJI = {"red": "🟥", "orange": "🟧", "green": "🟩", "blue": "🟦"}

FALLBACK = {
    "ls": (0.66, 0.27),
    "rs": (0.34, 0.27),
    "lh": (0.58, 0.58),
    "rh": (0.42, 0.58),
}


def ease_state(e):
    if e < 4:
        return "red", "Dar"
    if e < 6:
        return "orange", "Sınırda"
    if e <= 20:
        return "green", "Uygun"
    return "blue", "Bol"


def shoulder_state(d):
    if d < -1:
        return "red", "Dar"
    if d < 0:
        return "orange", "Sınırda"
    if d <= 4:
        return "green", "Tam oturur"
    return "blue", "Omuzdan düşer"


def length_state(d):
    if d < -3:
        return "orange", "Kısa"
    if d > 3:
        return "blue", "Uzun"
    return "green", "Uygun"


def find_landmarks(img):
    try:
        import mediapipe as mp
        arr = np.array(img.convert("RGB"))
        with mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1) as pose:
            res = pose.process(arr)
        if res.pose_landmarks:
            lm = res.pose_landmarks.landmark
            idx = {"ls": 11, "rs": 12, "lh": 23, "rh": 24}
            return {k: (lm[i].x, lm[i].y) for k, i in idx.items()}, True
    except Exception:
        pass
    return FALLBACK, False


def draw_zone(base, ellipses, color):
    w, h = base.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    for c, rx, ry in ellipses:
        draw.ellipse([c[0] - rx, c[1] - ry, c[0] + rx, c[1] + ry], fill=165)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(w, h) * 0.012))
    solid = Image.new("RGB", (w, h), COLORS[color])
    base.paste(solid, (0, 0), mask)


def build_heatmap(image_path, chart, size, chest, waist, shoulder, height):
    if size not in chart:
        size = list(chart.keys())[0]
    g = chart[size]
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    lm, found = find_landmarks(img)
    pts = {k: np.array([v[0] * w, v[1] * h]) for k, v in lm.items()}
    ls, rs, lh, rh = pts["ls"], pts["rs"], pts["lh"], pts["rh"]
    sh_mid = (ls + rs) / 2
    hip_mid = (lh + rh) / 2
    sh_w = abs(ls[0] - rs[0])
    hip_w = abs(lh[0] - rh[0])
    torso = max(hip_mid[1] - sh_mid[1], 1)
    body_w = max(hip_w, sh_w * 0.7)

    chest_c = np.array([sh_mid[0], sh_mid[1] + torso * 0.28])
    waist_c = np.array([sh_mid[0], sh_mid[1] + torso * 0.70])
    hem_c = np.array([hip_mid[0], hip_mid[1] + torso * 0.12])

    chest_ease = g["chest"] - chest
    waist_ease = g["chest"] - waist
    sh_diff = g["shoulder"] - shoulder
    len_diff = g["length"] - height * 0.40

    zones = []
    c, label = shoulder_state(sh_diff)
    zones.append(("Omuz", c, label, "{:+.1f} cm".format(sh_diff),
                  [(ls, sh_w * 0.22, sh_w * 0.16), (rs, sh_w * 0.22, sh_w * 0.16)]))
    c, label = ease_state(chest_ease)
    zones.append(("Göğüs", c, label, "{:+.1f} cm pay".format(chest_ease),
                  [(chest_c, sh_w * 0.42, torso * 0.16)]))
    c, label = ease_state(waist_ease)
    zones.append(("Bel", c, label, "{:+.1f} cm pay".format(waist_ease),
                  [(waist_c, body_w * 0.5, torso * 0.14)]))
    c, label = length_state(len_diff)
    zones.append(("Boy", c, label, "{:+.1f} cm".format(len_diff),
                  [(hem_c, body_w * 0.6, torso * 0.05)]))

    base = img.copy()
    for name, color, label, value, ellipses in zones:
        draw_zone(base, ellipses, color)

    lines = ["**" + size + " bedeni için bölge analizi**", "", "| Bölge | Durum | Fark |", "|---|---|---|"]
    for name, color, label, value, ellipses in zones:
        lines.append("| " + name + " | " + EMOJI[color] + " " + label + " | " + value + " |")
    if not found:
        lines.append("")
        lines.append("Not: Vücut iskeleti bulunamadığı için bölgeler yaklaşık konumlandı.")
    return base, "\n".join(lines)
