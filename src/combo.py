import os
from PIL import Image
from src.tryon import run_tryon


def run_layers(person_path, garment_paths, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    current = person_path
    steps = []
    for i, garment in enumerate(garment_paths):
        out = run_tryon(current, garment)
        saved = os.path.join(out_dir, "layer_" + str(i + 1) + ".png")
        Image.open(out).convert("RGB").save(saved, format="PNG")
        steps.append(saved)
        current = saved
    return current, steps
