import os
import shutil
import gradio as gr
from src.tryon import run_tryon
from src.fit import report, load_chart, DEFAULT_CHART
from src.compare import build_compare
from src.heatmap import build_heatmap

GARMENT_DIR = "assets/garments"
EXTS = (".jpg", ".jpeg", ".png", ".webp")
LEGEND = "🟥 Dar &nbsp;&nbsp; 🟧 Sınırda / kısa &nbsp;&nbsp; 🟩 Uygun &nbsp;&nbsp; 🟦 Bol / uzun"


def list_garments():
    if not os.path.isdir(GARMENT_DIR):
        return []
    return sorted(f for f in os.listdir(GARMENT_DIR) if f.lower().endswith(EXTS))


def garment_path(name):
    return os.path.join(GARMENT_DIR, name) if name else None


def update_preview(name):
    return garment_path(name)


def make_heat(image_path, garment_name, size, chest, waist, shoulder, height):
    os.makedirs("outputs", exist_ok=True)
    chart = load_chart(garment_name)
    heat_img, heat_md = build_heatmap(image_path, chart, size, chest, waist, shoulder, height)
    heat_path = os.path.join("outputs", "heatmap.png")
    heat_img.save(heat_path)
    return heat_path, heat_md


def analyze(person_path, garment_name, size, chest, waist, shoulder, height, preference):
    fit_text = report(size, garment_name, chest, waist, shoulder, height, preference)
    if person_path is None:
        return fit_text, None, ""
    heat_path, heat_md = make_heat(person_path, garment_name, size, chest, waist, shoulder, height)
    return fit_text, heat_path, heat_md


def tryon(person_path, garment_name, custom_garment, size, chest, waist, shoulder, height, preference):
    if person_path is None:
        raise gr.Error("Lütfen önce kendi fotoğrafını yükle.")
    chosen = custom_garment or garment_path(garment_name)
    if chosen is None:
        raise gr.Error("Katalogdan bir kıyafet seç veya kendi kıyafet fotoğrafını yükle.")
    os.makedirs("outputs", exist_ok=True)
    out = run_tryon(person_path, chosen)
    final = os.path.join("outputs", "result.png")
    shutil.copy(out, final)
    name = None if custom_garment else garment_name
    compare_html = build_compare(person_path, final)
    heat_path, heat_md = make_heat(final, name, size, chest, waist, shoulder, height)
    fit_text = report(size, name, chest, waist, shoulder, height, preference)
    return final, compare_html, fit_text, heat_path, heat_md


garments = list_garments()
sizes = list(DEFAULT_CHART.keys())

with gr.Blocks(title="Sanal Kabin") as demo:
    gr.Markdown("# Sanal Kabin\nFotoğrafını yükle, kıyafeti ve bedeni seç; hem görünümü hem beden uyumunu gör.")
    with gr.Row():
        with gr.Column():
            person = gr.Image(type="filepath", label="Senin fotoğrafın (karşıdan, ayakta, kollar yanda)")
            with gr.Row():
                height = gr.Slider(140, 210, value=175, step=1, label="Boy (cm)")
                chest = gr.Slider(70, 140, value=98, step=1, label="Göğüs çevresi (cm)")
            with gr.Row():
                shoulder = gr.Slider(30, 60, value=44, step=1, label="Omuz genişliği (cm)")
                waist = gr.Slider(50, 130, value=84, step=1, label="Bel çevresi (cm)")
        with gr.Column():
            garment_dd = gr.Dropdown(choices=garments, value=garments[0] if garments else None, label="Kıyafet kataloğu")
            preview = gr.Image(value=garment_path(garments[0]) if garments else None, label="Seçilen ürün", interactive=False)
            custom = gr.Image(type="filepath", label="Veya kendi kıyafet fotoğrafını yükle (opsiyonel)")
            size = gr.Radio(sizes, value="M", label="Denemek istediğin beden")
            pref = gr.Radio(["Vücuda oturan", "Normal", "Bol"], value="Normal", label="Kalıp tercihin")
            btn = gr.Button("Sanal kabinde dene", variant="primary")
            btn2 = gr.Button("Sadece beden analizi (hızlı)")
        with gr.Column():
            gr.Markdown("### Önce / Sonra (sürükleyerek karşılaştır)")
            compare = gr.HTML()
            result = gr.Image(label="Sonuç")
            gr.Markdown("### Beden uyum ısı haritası")
            gr.Markdown(LEGEND)
            heat_img = gr.Image(label="Isı haritası")
            heat_md = gr.Markdown()
            fit_md = gr.Markdown()
    garment_dd.change(update_preview, garment_dd, preview)
    btn.click(
        tryon,
        [person, garment_dd, custom, size, chest, waist, shoulder, height, pref],
        [result, compare, fit_md, heat_img, heat_md],
    )
    btn2.click(
        analyze,
        [person, garment_dd, size, chest, waist, shoulder, height, pref],
        [fit_md, heat_img, heat_md],
    )

if __name__ == "__main__":
    demo.launch(share=True)
