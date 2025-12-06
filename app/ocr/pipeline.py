import numpy as np
import torch
import cv2
import time
from PIL import Image
from app.ocr.adaptive_preprocessor import AdaptivePreprocessor
from app.ocr.dbnet_model import load_dbnet
from app.ocr.vietocr_model import load_vietocr, recognize_text
from segmentation.post_processing import get_post_processing
from addict import Dict
import yaml

# ---------------------------
# HÀM TIỆN ÍCH
# ---------------------------
def clamp(val, lo, hi):
    return max(lo, min(hi, val))

# ---------------------------
# NHÓM LINES THEO Y (median-height based)
# ---------------------------
def group_lines_by_median(boxes, med_h_factor=0.6):
    """
    boxes: list of [x1,y1,x2,y2]
    Trả về: list of lines, mỗi line là list of boxes (kept as [x1,y1,x2,y2])
    """
    if not boxes:
        return []

    arr = np.array(boxes, dtype=float)
    y_centers = (arr[:,1] + arr[:,3]) / 2.0
    heights = (arr[:,3] - arr[:,1])
    median_h = float(np.median(heights)) if len(heights)>0 else 0.0
    if median_h <= 0:
        median_h = float(np.mean(heights)) if len(heights)>0 else 10.0

    # sort by y_center
    order = np.argsort(y_centers)
    arr_sorted = arr[order]

    y_thresh = median_h * med_h_factor

    lines = []
    current = [arr_sorted[0].tolist()]
    current_mean_y = y_centers[order[0]]

    for r in arr_sorted[1:]:
        cy = (r[1] + r[3]) / 2.0
        if abs(cy - current_mean_y) <= y_thresh:
            current.append(r.tolist())
            # update mean
            current_mean_y = np.mean([ (b[1]+b[3])/2.0 for b in current ])
        else:
            lines.append(current)
            current = [r.tolist()]
            current_mean_y = cy
    lines.append(current)

    # Merge very close lines (to avoid over-splitting)
    merged = []
    for ln in lines:
        if not merged:
            merged.append(ln)
            continue
        prev = merged[-1]
        prev_y = np.mean([ (b[1]+b[3])/2.0 for b in prev ])
        cur_y = np.mean([ (b[1]+b[3])/2.0 for b in ln ])
        if abs(cur_y - prev_y) < median_h * 0.45:  # merge threshold
            merged[-1].extend(ln)
        else:
            merged.append(ln)

    # inside each line sort boxes by x1 ascending (left -> right)
    final_lines = []
    for ln in merged:
        ln_sorted = sorted(ln, key=lambda b: b[0])
        final_lines.append([ [int(b[0]), int(b[1]), int(b[2]), int(b[3])] for b in ln_sorted ])

    return final_lines

# ---------------------------
# PHÁT HIỆN CỘT BẰNG GAP TRÊN X_CENTER
# ---------------------------
def detect_columns_by_x_gaps(lines, min_gap_factor=1.5):
    """
    lines: list of lines (each is list of boxes [x1,y1,x2,y2])
    Ý tưởng: compute x_center for each line (mean of boxes), sort them; 
    find big gaps -> define column boundaries
    Trả về: list of columns, mỗi column là list of lines
    """
    if not lines:
        return []

    line_centers = [ np.mean([ (b[0]+b[2])/2.0 for b in line ]) for line in lines ]
    sorted_idx = np.argsort(line_centers)
    centers_sorted = [line_centers[i] for i in sorted_idx]

    # nếu ít lines thì 1 cột
    if len(centers_sorted) < 4:
        return [ [lines[i] for i in sorted_idx] ]

    # compute gaps between adjacent centers
    gaps = [ centers_sorted[i+1] - centers_sorted[i] for i in range(len(centers_sorted)-1) ]
    median_gap = np.median(gaps) if gaps else 0.0
    if median_gap <= 0:
        median_gap = np.mean(gaps) if gaps else 50.0

    # find split points where gap is significantly larger than typical
    split_indices = []
    threshold = median_gap * min_gap_factor
    for i,g in enumerate(gaps):
        if g > threshold:
            split_indices.append(i)

    # build boundaries over sorted_idx
    columns = []
    start = 0
    for si in split_indices:
        group_idx = sorted_idx[start:si+1]
        columns.append([ lines[i] for i in group_idx ])
        start = si+1
    # last group
    group_idx = sorted_idx[start: len(sorted_idx)]
    columns.append([ lines[i] for i in group_idx ])

    # sort lines inside each column by y (top -> bottom)
    for col in columns:
        col.sort(key=lambda ln: np.mean([ (b[1]+b[3])/2.0 for b in ln ]))

    # sort columns left -> right by their mean x center
    columns.sort(key=lambda col: np.mean([ np.mean([ (b[0]+b[2])/2.0 for b in ln ]) for ln in col for b in ln ]))
    return columns

# ---------------------------
# TOÀN BỘ PIPELINE SẮP XẾP (LEFT->RIGHT reading order)
# ---------------------------
def sort_boxes_reading_order(boxes):
    """
    boxes: list of [x1,y1,x2,y2]
    Trả về: final_lines_ordered: list of lines (each line list of boxes)
    Reading order implemented: iterate columns left->right, within column top->bottom
    """
    # 1) group into lines
    lines = group_lines_by_median(boxes, med_h_factor=0.6)

    # 2) detect columns using x gaps
    columns = detect_columns_by_x_gaps(lines, min_gap_factor=1.6)

    # 3) final assembly: for each column left->right, append its lines in top->bottom
    final_lines = []
    for col in columns:
        # col already sorted by y
        for ln in col:
            # ensure boxes inside line sorted left->right
            ln_sorted = sorted(ln, key=lambda b: b[0])
            final_lines.append(ln_sorted)

    return final_lines

class OCRPipeline:
    def __init__(self, dbnet_weight, dbnet_cfg, vietocr_cfg, vietocr_weight):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load DBNet
        self.dbnet = load_dbnet(dbnet_weight, dbnet_cfg, self.device)
        
        # Load VietOCR
        self.vietocr = load_vietocr(vietocr_cfg, vietocr_weight, str(self.device))
        
        # Load Preprocessor
        self.preprocessor = AdaptivePreprocessor()
        
        # Load Post Processing config
        with open(dbnet_cfg, "r") as f:
            cfg = Dict(yaml.safe_load(f))
        self.post_process = get_post_processing(cfg["post_processing"])

    def process(self, image_bytes):
        start = time.time()
        
        # 1. Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Could not decode image")
            
        orig_h, orig_w = img_bgr.shape[:2]
        
        # 2. Preprocess
        img_tensor, preprocessed_bgr, (target_h, target_w) = self.preprocessor.preprocess(img_bgr, 736)
        img_tensor = img_tensor.to(self.device)
        
        # 3. DBNet Inference
        with torch.no_grad():
            preds = self.dbnet(img_tensor)
            
        # 4. Post Process (Get Boxes)
        batch = {"shape": [(orig_h, orig_w)]}
        boxes_list, scores = self.post_process(batch, preds, is_output_polygon=False)
        boxes = boxes_list[0] # First image in batch
        
        # 5. Sort Boxes
        # Convert boxes to list of [x1, y1, x2, y2]
        boxes_xyxy = []
        for box in boxes:
            # box is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]] (polygon) or similar
            # We need bounding rect [x1, y1, x2, y2]
            xs = [pt[0] for pt in box]
            ys = [pt[1] for pt in box]
            x1, x2 = int(min(xs)), int(max(xs))
            y1, y2 = int(min(ys)), int(max(ys))
            
            x1 = clamp(x1, 0, orig_w-1)
            x2 = clamp(x2, 0, orig_w-1)
            y1 = clamp(y1, 0, orig_h-1)
            y2 = clamp(y2, 0, orig_h-1)
            
            if x2 > x1 and y2 > y1:
                boxes_xyxy.append([x1, y1, x2, y2])
                
        lines = sort_boxes_reading_order(boxes_xyxy)
        
        # 6. Recognize Text (VietOCR)
        results = []
        final_lines_texts = []
        
        for ln in lines:
            line_texts = []
            for (x1,y1,x2,y2) in ln:
                crop = img_bgr[y1:y2, x1:x2]
                if crop.size == 0:
                    continue
                
                crop_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                text = recognize_text(self.vietocr, crop_pil)
                
                results.append({
                    "bbox": [x1, y1, x2, y2],
                    "text": text
                })
                
                if text:
                    line_texts.append(text)
            
            final_lines_texts.append(" ".join(line_texts))
            
        full_text = "\n".join([ln for ln in final_lines_texts if ln.strip() != ""])
        
        return {
            "results": results,
            "full_text": full_text,
            "processing_time": time.time()-start
        }
