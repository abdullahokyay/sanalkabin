import numpy as np
from PIL import Image, ImageDraw

_models = {}
VISIBLE = 0.3


class Pt:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Landmarks:
    def __init__(self, pts):
        self.landmark = pts


class Result:
    def __init__(self, landmarks, mask):
        self.pose_landmarks = landmarks
        self.segmentation_mask = mask


def load_models():
    if not _models:
        from ultralytics import YOLO
        _models["pose"] = YOLO("yolov8m-pose.pt")
        _models["seg"] = YOLO("yolov8m-seg.pt")
    return _models["pose"], _models["seg"]


def biggest_index(result):
    if result.boxes is None or len(result.boxes) == 0:
        return None
    xyxy = result.boxes.xyxy.cpu().numpy()
    areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])
    return int(np.argmax(areas))


def run_pose(img):
    pose_model, seg_model = load_models()
    img = img.convert("RGB")
    w, h = img.size

    landmarks = None
    pres = pose_model(img, verbose=False)[0]
    pi = biggest_index(pres)
    if pi is not None and pres.keypoints is not None:
        xy = pres.keypoints.xy[pi].cpu().numpy()
        conf = pres.keypoints.conf
        conf = conf[pi].cpu().numpy() if conf is not None else np.ones(len(xy))
        needed = [5, 6, 11, 12]
        if all(conf[i] >= VISIBLE for i in needed):
            pts = [Pt(0.5, 0.5) for _ in range(33)]
            mapping = {11: 5, 12: 6, 23: 11, 24: 12}
            for mp_idx, coco_idx in mapping.items():
                pts[mp_idx] = Pt(float(xy[coco_idx][0]) / w, float(xy[coco_idx][1]) / h)
            landmarks = Landmarks(pts)

    mask = None
    sres = seg_model(img, classes=[0], verbose=False)[0]
    si = biggest_index(sres)
    if si is not None and sres.masks is not None:
        poly = sres.masks.xy[si]
        if len(poly) >= 3:
            canvas = Image.new("L", (w, h), 0)
            ImageDraw.Draw(canvas).polygon([tuple(p) for p in poly.tolist()], fill=255)
            mask = np.array(canvas).astype(np.float32) / 255.0

    return Result(landmarks, mask)
