from src.pose import run_pose
import math
import numpy as np
from PIL import Image, ImageDraw

SHOULDER_K = 0.95
CHEST_K = 1.06
WAIST_K = 1.06
CHEST_DEPTH = 0.72
WAIST_DEPTH = 0.75
ARMS_ATTACHED_RATIO = 0.9
CHEST_FALLBACK = 0.76
WAIST_FALLBACK = 0.68


def perimeter(width, depth):
    a = width / 2.0
    b = depth / 2.0
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))


def run_at(mask, y, x_mid):
    y = int(min(max(y, 0), mask.shape[0] - 1))
    row = mask[y].astype(np.int8)
    if not row.any():
        return None
    padded = np.concatenate(([0], row, [0]))
    diff = np.diff(padded)
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0] - 1
    for s, e in zip(starts, ends):
        if s <= x_mid <= e:
            return int(s), int(e)
    dists = [min(abs(s - x_mid), abs(e - x_mid)) for s, e in zip(starts, ends)]
    i = int(np.argmin(dists))
    return int(starts[i]), int(ends[i])


def estimate(image_path, height_cm):
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    res = run_pose(img)
    if res.pose_landmarks is None or res.segmentation_mask is None:
        raise RuntimeError("Fotoğrafta vücut bulunamadı. Boydan ve karşıdan çekilmiş bir fotoğraf kullan.")

    mask = res.segmentation_mask > 0.5
    rows = np.where(mask.any(axis=1))[0]
    if len(rows) == 0:
        raise RuntimeError("Vücut maskesi çıkarılamadı. Daha net bir fotoğraf dene.")

    top, bottom = int(rows[0]), int(rows[-1])
    px_h = max(bottom - top, 1)
    cm_per_px = height_cm / px_h
    warnings = []
    if top <= 2 or bottom >= h - 3:
        warnings.append("Başın veya ayakların kadrajın dışında kalmış olabilir, boy kalibrasyonu sapabilir.")
    if px_h < h * 0.55:
        warnings.append("Vücut fotoğrafta küçük görünüyor, daha yakından veya boydan çekersen sonuç iyileşir.")

    lm = res.pose_landmarks.landmark

    def pt(i):
        return np.array([lm[i].x * w, lm[i].y * h])

    ls, rs, lh, rh = pt(11), pt(12), pt(23), pt(24)
    sh_mid = (ls + rs) / 2
    hip_mid = (lh + rh) / 2
    x_mid = (sh_mid[0] + hip_mid[0]) / 2
    torso = max(hip_mid[1] - sh_mid[1], 1)

    best = 0
    sh_row = int(sh_mid[1])
    sh_run = None
    for y in range(int(sh_mid[1]), int(sh_mid[1] + torso * 0.06) + 1):
        r = run_at(mask, y, x_mid)
        if r and (r[1] - r[0]) > best:
            best = r[1] - r[0]
            sh_row = y
            sh_run = r
    if sh_run is None:
        raise RuntimeError("Omuz hattı bulunamadı. Fotoğrafı kontrol et.")
    shoulder_px = best

    def width_at(y_ratio, fallback):
        y = int(sh_mid[1] + torso * y_ratio)
        r = run_at(mask, y, x_mid)
        if r is None:
            return y, shoulder_px * fallback, True
        px = r[1] - r[0]
        if px > ARMS_ATTACHED_RATIO * shoulder_px:
            return y, shoulder_px * fallback, True
        return y, float(px), False

    chest_y, chest_px, chest_est = width_at(0.25, CHEST_FALLBACK)
    waist_y, waist_px, waist_est = width_at(0.70, WAIST_FALLBACK)
    if chest_est or waist_est:
        warnings.append("Kollar gövdeye yakın olduğu için göğüs ve bel oranla tahmin edildi. Kollarını hafif açarak çekersen daha doğru olur.")

    shoulder_cm = shoulder_px * cm_per_px * SHOULDER_K
    chest_w = chest_px * cm_per_px
    waist_w = waist_px * cm_per_px
    chest_cm = perimeter(chest_w, chest_w * CHEST_DEPTH) * CHEST_K
    waist_cm = perimeter(waist_w, waist_w * WAIST_DEPTH) * WAIST_K

    out = img.copy()
    draw = ImageDraw.Draw(out)
    lw = max(3, w // 250)

    def hline(y, x0, x1, color, label):
        draw.line([(x0, y), (x1, y)], fill=color, width=lw)
        draw.text((min(x1 + 8, w - 160), y - 14), label, fill=color)

    hline(sh_row, sh_run[0], sh_run[1], (40, 190, 90), "Omuz {:.0f} cm".format(shoulder_cm))
    hline(chest_y, int(x_mid - chest_px / 2), int(x_mid + chest_px / 2), (245, 150, 30), "Gogus {:.0f} cm".format(chest_cm))
    hline(waist_y, int(x_mid - waist_px / 2), int(x_mid + waist_px / 2), (230, 40, 40), "Bel {:.0f} cm".format(waist_cm))
    draw.line([(8, top), (8, bottom)], fill=(50, 120, 235), width=lw)
    draw.text((14, (top + bottom) // 2), "Boy {:.0f} cm".format(height_cm), fill=(50, 120, 235))

    values = {"shoulder": shoulder_cm, "chest": chest_cm, "waist": waist_cm}
    return values, out, warnings
