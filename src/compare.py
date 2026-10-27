import base64
import io
from PIL import Image

STYLE = """<style>
.cmp{position:relative;width:100%;max-width:520px;margin:0 auto;overflow:hidden;border-radius:12px;--pos:50%}
.cmp img{position:absolute;inset:0;width:100%;height:100%;object-fit:fill;display:block}
.cmp .after{clip-path:inset(0 0 0 var(--pos))}
.cmp .line{position:absolute;top:0;bottom:0;left:var(--pos);width:3px;margin-left:-1px;background:#fff;box-shadow:0 0 6px rgba(0,0,0,.6);pointer-events:none}
.cmp .tag{position:absolute;top:10px;padding:3px 10px;border-radius:999px;background:rgba(0,0,0,.55);color:#fff;font:600 13px sans-serif;pointer-events:none}
.cmp .tag.l{left:10px}
.cmp .tag.r{right:10px}
.cmp input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
</style>"""

TEMPLATE = """<div class="cmp" style="aspect-ratio:__W__/__H__"><img class="before" src="data:image/jpeg;base64,__BEFORE__"><img class="after" src="data:image/jpeg;base64,__AFTER__"><div class="line"></div><span class="tag l">Önce</span><span class="tag r">Sonra</span><input type="range" min="0" max="100" value="50" oninput="this.parentNode.style.setProperty('--pos', this.value + '%')"></div>"""


def to_b64(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def build_compare(before_path, after_path):
    after = Image.open(after_path).convert("RGB")
    before = Image.open(before_path).convert("RGB").resize(after.size)
    w, h = after.size
    html = TEMPLATE
    html = html.replace("__W__", str(w)).replace("__H__", str(h))
    html = html.replace("__BEFORE__", to_b64(before)).replace("__AFTER__", to_b64(after))
    return STYLE + html
