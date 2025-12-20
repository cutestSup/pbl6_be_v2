import numpy as np
import torch
import cv2
import time
from PIL import Image

# Fix for hanging on low-resource/cloud environments
cv2.setNumThreads(0)
torch.set_num_threads(1)

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

def postprocess_text(text):
    if not text: return ""
    text = text.strip()
    replacements = {'|': 'I', '[': '(', ']': ')'}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

# ---------------------------
# THUẬT TOÁN SẮP XẾP READING ORDER - DỰA VÀO Y CENTER
# ---------------------------
def sort_boxes_reading_order(boxes):
    """
    Sắp xếp boxes theo Y center với tolerance nhỏ.
    """
    if not boxes: return []
    
    # Filter small boxes
    clean_boxes = []
    for b in boxes:
        if len(b) < 4: continue
        x1, y1, x2, y2 = b[:4]
        if x2 > x1 and y2 > y1 and (x2 - x1) >= 2 and (y2 - y1) >= 2:
            if x1 == 0 and y1 == 0 and x2 == 0 and y2 == 0:
                continue
            clean_boxes.append([x1, y1, x2, y2])
    if not clean_boxes: return []
    
    heights = [b[3] - b[1] for b in clean_boxes]
    avg_h = np.median(heights) if heights else 10
    # print(f"Median Box Height: {avg_h:.2f}")
    
    # Tính Y center cho mỗi box
    boxes_with_cy = [(b, (b[1] + b[3]) / 2) for b in clean_boxes]
    boxes_with_cy.sort(key=lambda x: (x[1], x[0][0]))  # Sort theo cy, rồi x1
    
    # Gom dòng: tìm dòng GẦN NHẤT có Y center distance <= 11 pixels
    lines = []
    threshold = 11.3
    
    for box, cy in boxes_with_cy:
        # Tìm dòng GẦN NHẤT trong ngưỡng
        best_line_idx = -1
        best_distance = threshold + 1
        
        for idx, line in enumerate(lines):
            line_cy_avg = np.mean([(b[1] + b[3]) / 2 for b in line])
            distance = abs(cy - line_cy_avg)
            
            if distance <= threshold and distance < best_distance:
                best_distance = distance
                best_line_idx = idx
        
        if best_line_idx >= 0:
            lines[best_line_idx].append(box)
        else:
            lines.append([box])
    
    # Sắp xếp dòng theo Y, boxes trong dòng theo X
    lines.sort(key=lambda line: np.mean([b[1] for b in line]))
    
    final_lines = []
    for line in lines:
        line.sort(key=lambda b: b[0])
        final_lines.append(line)
    
    # print(f"Đã gom thành {len(final_lines)} dòng")
    
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
        # Reduced from 736 to 640 to prevent hanging on server
        img_tensor, preprocessed_bgr, (target_h, target_w) = self.preprocessor.preprocess(img_bgr, 640)
        img_tensor = img_tensor.to(self.device)
        
        # 3. DBNet Inference
        # print("🔍 Running DBNet inference...")
        with torch.no_grad():
            preds = self.dbnet(img_tensor)
        # print("✅ DBNet inference done.")
            
        # 4. Post Process (Get Boxes)
        # print("⚙️ Post-processing boxes...")
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
        # print(f"📖 Recognizing text for {len(lines)} lines...")
        results = []
        final_lines_texts = []
        
        for i, ln in enumerate(lines):
            line_texts = []
            for (x1,y1,x2,y2) in ln:
                crop = img_bgr[y1:y2, x1:x2]
                if crop.size == 0:
                    continue
                
                crop_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                text = recognize_text(self.vietocr, crop_pil)
                text = postprocess_text(text)
                
                results.append({
                    "bbox": [x1, y1, x2, y2],
                    "text": text
                })
                
                if text:
                    line_texts.append(text)
            
            final_lines_texts.append(" ".join(line_texts))
            # if i % 5 == 0:
            #     print(f"   Processed line {i+1}/{len(lines)}")
        
        # print("✅ OCR process completed.")
        full_text = "\n".join([ln for ln in final_lines_texts if ln.strip() != ""])
        
        return {
            "results": results,
            "full_text": full_text,
            "processing_time": time.time()-start
        }
