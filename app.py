import os
import shutil
import gradio as gr
from src.tryon import run_tryon

GARMENT_DIR = "assets/garments"
EXTS = (".jpg", ".jpeg", ".png", ".webp")

def list_garments():
    if not os.path.isdir(GARMENT_DIR):
        return []
    return sorted(f for f in os.listdir(GARMENT_DIR) if f.lower().endswith(EXTS))

def garment_path(name):
    return os.path.join(GARMENT_DIR, name) if name else None

def update_preview(name):
    return garment_path(name)

def tryon(person_path, garment_name, custom_garment, height, weight, shoulder, waist):
    if person_path is None:
        raise gr.Error("Lutfen once kendi fotografini yukle.")
    chosen = custom_garment or garment_path(garment_name)
    if chosen is None:
        raise gr.Error("Katalogdan bir kiyafet sec veya kendi kiyafet fotografini yukle.")
    os.makedirs("outputs", exist_ok=True)
    out = run_tryon(person_path, chosen)
    final = os.path.join("outputs", "result.png")
    shutil.copy(out, final)
    info = f"Tamamlandi. Olculer: boy {height} cm, kilo {weight} kg, omuz {shoulder} cm, bel {waist} cm"
    return final, info

garments = list_garments()

with gr.Blocks(title="Sanal Kabin") as demo:
    gr.Markdown("# Sanal Kabin\nFotografini yukle, kiyafeti sec, ayni kisinin o kiyafeti giymis halini gor.")
    with gr.Row():
        with gr.Column():
            person = gr.Image(type="filepath", label="Senin fotografin (karsidan, ayakta, kollar yanda)")
            with gr.Row():
                height = gr.Slider(140, 210, value=175, step=1, label="Boy (cm)")
                weight = gr.Slider(40, 140, value=70, step=1, label="Kilo (kg)")
            with gr.Row():
                shoulder = gr.Slider(30, 60, value=44, step=1, label="Omuz (cm)")
                waist = gr.Slider(50, 120, value=78, step=1, label="Bel (cm)")
        with gr.Column():
            garment_dd = gr.Dropdown(choices=garments, value=garments[0] if garments else None, label="Kiyafet katalogu")
            preview = gr.Image(value=garment_path(garments[0]) if garments else None, label="Secilen urun", interactive=False)
            custom = gr.Image(type="filepath", label="Veya kendi kiyafet fotografini yukle (opsiyonel)")
            btn = gr.Button("Sanal kabinde dene", variant="primary")
        with gr.Column():
            result = gr.Image(label="Sonuc")
            status = gr.Textbox(label="Durum", interactive=False)
    garment_dd.change(update_preview, garment_dd, preview)
    btn.click(tryon, [person, garment_dd, custom, height, weight, shoulder, waist], [result, status])

if __name__ == "__main__":
    demo.launch(share=True)
