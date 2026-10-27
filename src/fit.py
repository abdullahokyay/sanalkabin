import json
import os

DEFAULT_CHART = {
    "S":   {"chest": 100, "shoulder": 44, "length": 68},
    "M":   {"chest": 104, "shoulder": 46, "length": 70},
    "L":   {"chest": 108, "shoulder": 48, "length": 72},
    "XL":  {"chest": 112, "shoulder": 50, "length": 74},
    "XXL": {"chest": 116, "shoulder": 52, "length": 76},
}

TARGET_EASE = {"Vücuda oturan": 8, "Normal": 14, "Bol": 24}
MIN_EASE = 4


def load_chart(garment_name):
    if garment_name:
        base = os.path.splitext(os.path.join("assets/garments", garment_name))[0]
        path = base + ".json"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return DEFAULT_CHART


def ease_label(ease):
    if ease < MIN_EASE:
        return "Dar"
    if ease < 10:
        return "Vücuda oturan"
    if ease < 20:
        return "Normal / rahat"
    return "Bol / oversize"


def evaluate(size, chart, chest, waist, shoulder, height):
    g = chart[size]
    body = max(chest, waist)
    ease = g["chest"] - body
    sh_diff = g["shoulder"] - shoulder
    ideal_len = height * 0.40
    len_diff = g["length"] - ideal_len

    if sh_diff < -1:
        sh_note = "Omuz dar gelir, omuz ve kol başında sıkma yapabilir."
    elif sh_diff <= 3:
        sh_note = "Omuz çizgisi tam oturur."
    else:
        sh_note = "Omuz çizgisi omuzdan aşağı düşer, geniş duruş verir."

    if len_diff < -3:
        len_note = "Boy kısa kalır."
    elif len_diff > 3:
        len_note = "Boy uzun gelir."
    else:
        len_note = "Boy uygun."

    return {"size": size, "ease": ease, "label": ease_label(ease),
            "sh_diff": sh_diff, "sh_note": sh_note, "len_note": len_note}


def recommend(chart, chest, waist, shoulder, height, preference):
    target = TARGET_EASE.get(preference, 14)
    results = [evaluate(s, chart, chest, waist, shoulder, height) for s in chart]
    ok = [r for r in results if r["ease"] >= MIN_EASE and r["sh_diff"] >= -1]
    if not ok:
        ok = [r for r in results if r["ease"] >= MIN_EASE]
    if not ok:
        return results[-1]["size"], results
    best = min(ok, key=lambda r: abs(r["ease"] - target))
    return best["size"], results


def report(size, garment_name, chest, waist, shoulder, height, preference):
    chart = load_chart(garment_name)
    if size not in chart:
        size = list(chart.keys())[0]
    chosen = evaluate(size, chart, chest, waist, shoulder, height)
    rec, results = recommend(chart, chest, waist, shoulder, height, preference)

    lines = []
    lines.append("### " + size + " bedeni sende **" + chosen["label"].lower() + "** durur")
    lines.append("- Göğüs/bel payı: **" + str(round(chosen["ease"], 1)) + " cm**")
    lines.append("- " + chosen["sh_note"])
    lines.append("- " + chosen["len_note"])
    lines.append("")
    if rec == size:
        lines.append("**Seçtiğin " + size + " bedeni '" + preference.lower() + "' tercihine uygun.**")
    else:
        lines.append("**'" + preference + "' kalıp için önerim: " + rec + " beden.**")
    lines.append("")
    lines.append("| Beden | Pay (cm) | Duruş | Omuz |")
    lines.append("|---|---|---|---|")
    for r in results:
        mark = " (önerilen)" if r["size"] == rec else ""
        lines.append("| " + r["size"] + mark + " | " + str(round(r["ease"], 1)) + " | " + r["label"] + " | " + r["sh_note"] + " |")
    return "\n".join(lines)
