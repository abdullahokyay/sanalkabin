import os
from gradio_client import Client, handle_file

SPACE = "yisol/IDM-VTON"
_client = None

def get_client():
    global _client
    if _client is None:
        token = None
        try:
            from google.colab import userdata
            token = userdata.get("HF_TOKEN")
        except Exception:
            token = os.environ.get("HF_TOKEN")
        _client = Client(SPACE, hf_token=token) if token else Client(SPACE)
    return _client

def run_tryon(person_path, garment_path, garment_des="clothing", steps=30, seed=42):
    client = get_client()
    result = client.predict(
        dict={"background": handle_file(person_path), "layers": [], "composite": None},
        garm_img=handle_file(garment_path),
        garment_des=garment_des,
        is_checked=True,
        is_checked_crop=False,
        denoise_steps=steps,
        seed=seed,
        api_name="/tryon",
    )
    return result[0]
