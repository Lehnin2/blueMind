# utils/predictor.py
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.utils.visualizer import Visualizer, ColorMode
from detectron2.data import MetadataCatalog
import cv2
import torch
import numpy as np
from app.utils.coin_detector import detect_coin
from detectron2.utils.visualizer import Visualizer
import numpy as np
import torch
import cv2
import math

def get_metadata():
    return MetadataCatalog.get("fish_valid")

def get_predictor():
    from detectron2.config import get_cfg
    from detectron2 import model_zoo

    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-Keypoints/keypoint_rcnn_R_50_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
    cfg.MODEL.ROI_KEYPOINT_HEAD.NUM_KEYPOINTS = 2
    cfg.MODEL.WEIGHTS = "app/models/fish/model_fishonly_0016499.pth"
    cfg.MODEL.DEVICE = "cpu"
    cfg.MODEL.KEYPOINT_ON = True
    predictor = DefaultPredictor(cfg)
    return predictor


COIN_DIAMETER_MM = 28.0

def euclidean(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)


def run_prediction(predictor, image_path,return_length_mm=False):
    metadata = MetadataCatalog.get("fish_valid")

    # Load image and make copies to avoid interference
    im_original = cv2.imread(image_path)
    im_for_fish = im_original.copy()
    im_for_coin = im_original.copy()
    im_output = im_original.copy()  # We'll draw on this

    # --- Fish detection using Detectron2 ---
    outputs = predictor(im_for_fish)
    instances = outputs["instances"].to("cpu")

    # --- FISH KEYPOINT LOGIC ---
    best_index = -1
    max_spread = -1
    best_kpts = None

    for i, kpts in enumerate(instances.pred_keypoints):
        if kpts.shape[1] > 2:
            visible = kpts[kpts[:, 2] > 0.5][:, :2]
        else:
            visible = kpts[:, :2]
        if len(visible) >= 2:
            spread = torch.max(visible[:, 0]) - torch.min(visible[:, 0]) + torch.max(visible[:, 1]) - torch.min(visible[:, 1])
            if spread > max_spread:
                max_spread = spread
                best_index = i
                best_kpts = kpts

    if best_kpts is not None:
        fish_point1 = best_kpts[0][:2].tolist()
        fish_point2 = best_kpts[1][:2].tolist()
        fish_pixel_len = euclidean(fish_point1, fish_point2)
    else:
        fish_pixel_len = None

    # --- Coin detection using YOLO ---
    coin_box, coin_conf = detect_coin(im_for_coin)
    if coin_box:
        x1, y1, x2, y2 = coin_box
        coin_pixel_diameter = euclidean((x1, y1), (x2, y2))
        px_per_mm = coin_pixel_diameter / COIN_DIAMETER_MM
        fish_length_mm = fish_pixel_len / px_per_mm if fish_pixel_len else None

        # Draw coin box
        cv2.rectangle(im_output, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(im_output, f"Coin ({coin_pixel_diameter:.1f}px)", (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    else:
        fish_length_mm = None
        cv2.putText(im_output, "Coin not detected", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # --- Draw fish keypoints line ---
    if best_kpts is not None:
        x1, y1 = map(int, fish_point1)
        x2, y2 = map(int, fish_point2)
        cv2.line(im_output, (x1, y1), (x2, y2), (255, 0, 0), 2)

        if fish_length_mm:
            cv2.putText(im_output, f"Fish: {fish_length_mm:.1f} mm", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        else:
            # Still show pixel length if no coin
            cv2.putText(im_output, f"Fish: {fish_pixel_len:.1f} px", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 255), 2)

    return im_output, fish_length_mm  # instead of just return im_output


