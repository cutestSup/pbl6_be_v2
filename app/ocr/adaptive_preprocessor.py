import cv2
import numpy as np
import torch

class AdaptivePreprocessor:
    def __init__(self):
        self.base_strategies = {
            'very_dark': {'clahe_clip': 8.0, 'tile': (8, 8), 'bilateral': (7, 50, 50), 'denoise': (10, 10, 7, 21)},
            'dark': {'clahe_clip': 6.0, 'tile': (8, 8), 'bilateral': (7, 40, 40), 'denoise': (10, 10, 7, 21)},
            'normal': {'clahe_clip': 3.0, 'tile': (16, 16), 'bilateral': (5, 30, 30), 'denoise': (5, 5, 3, 10)},
            'bright': {'clahe_clip': 1.5, 'tile': (16, 16), 'bilateral': (5, 20, 20), 'denoise': (5, 5, 3, 10)},
            'very_bright': {'clahe_clip': 1.0, 'tile': (16, 16), 'bilateral': (3, 15, 15), 'denoise': (5, 5, 3, 10)},
        }
    
    def analyze_image(self, img_bgr):
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        h, w = img_bgr.shape[:2]
        
        mean = np.mean(gray)
        std = np.std(gray)
        percentile_5 = np.percentile(gray, 5)
        percentile_95 = np.percentile(gray, 95)
        contrast = percentile_95 - percentile_5
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return {
            'mean': mean,
            'std': std,
            'percentile_5': percentile_5,
            'percentile_95': percentile_95,
            'contrast': contrast,
            'laplacian_var': laplacian_var,
            'shape': (h, w),
            'gray': gray
        }
    
    def classify_image(self, metrics):
        mean = metrics['mean']
        contrast = metrics['contrast']
        laplacian_var = metrics['laplacian_var']
        
        if mean < 50:
            primary = 'very_dark'
        elif mean < 100:
            primary = 'dark'
        elif mean < 150:
            primary = 'normal'
        elif mean < 200:
            primary = 'bright'
        else:
            primary = 'very_bright'
        
        return primary, {
            'is_high_contrast': contrast > 100,
            'is_low_contrast': contrast < 50,
            'is_blur': laplacian_var < 80,
            'is_clear': laplacian_var > 1000,
        }
    
    def adapt_strategy(self, primary, characteristics):
        strategy = self.base_strategies[primary].copy()
        
        if characteristics['is_high_contrast']:
            strategy['clahe_clip'] = min(strategy['clahe_clip'] * 1.5, 8.0)
            d, s1, s2 = strategy['bilateral']
            strategy['bilateral'] = (d, min(s1 + 10, 70), min(s2 + 10, 70))
        
        if characteristics['is_low_contrast']:
            strategy['clahe_clip'] = min(strategy['clahe_clip'] * 2.0, 8.0)
            strategy['tile'] = (8, 8)
        
        if characteristics['is_blur']:
            strategy['clahe_clip'] = max(strategy['clahe_clip'] * 0.7, 0.5)
            d, s1, s2 = strategy['bilateral']
            strategy['bilateral'] = (d, max(s1 - 10, 5), max(s2 - 10, 5))
        
        if characteristics['is_clear']:
            d, s1, s2 = strategy['bilateral']
            strategy['bilateral'] = (d, min(s1 + 20, 80), min(s2 + 20, 80))
        
        return strategy
    
    def preprocess(self, img_bgr, short_size=736, img_name=None):
        metrics = self.analyze_image(img_bgr)
        primary, characteristics = self.classify_image(metrics)
        strategy = self.adapt_strategy(primary, characteristics)
        
        # print(f"{primary.upper()}", end="")
        # if characteristics['is_high_contrast']: print(" + high_contrast", end="")
        # if characteristics['is_low_contrast']: print(" + low_contrast", end="")
        # if characteristics['is_blur']: print(" + blur", end="")
        # if characteristics['is_clear']: print(" + clear", end="")
        # print(f"Brightness={metrics['mean']:.0f}, Contrast={metrics['contrast']:.0f}")
        
        gray = metrics['gray']
        
        h, w = img_bgr.shape[:2]
        scale = short_size * 1.0 / min(h, w)
        new_h = int(h * scale + 0.5)
        new_w = int(w * scale + 0.5)
        new_h = (new_h + 31) // 32 * 32
        new_w = (new_w + 31) // 32 * 32
        gray = cv2.resize(gray, (new_w, new_h))
        
        # === BƯỚC 1: Normalize ===
        if primary in ['very_dark', 'dark']:
            gray = cv2.normalize(gray, None, alpha=40, beta=220, norm_type=cv2.NORM_MINMAX)
        elif primary in ['very_bright', 'bright']:
            gray = cv2.normalize(gray, None, alpha=50, beta=230, norm_type=cv2.NORM_MINMAX)
        else:
            gray = cv2.normalize(gray, None, alpha=30, beta=220, norm_type=cv2.NORM_MINMAX)
        
        # === BƯỚC 2: CLAHE ===
        clahe = cv2.createCLAHE(clipLimit=strategy['clahe_clip'], tileGridSize=strategy['tile'])
        gray = clahe.apply(gray)
        
        # === BƯỚC 3: Bilateral Filter ===
        d, sigma1, sigma2 = strategy['bilateral']
        gray = cv2.bilateralFilter(gray, d, sigma1, sigma2)
        
        # === BƯỚC 4: Morphological Operations ===
        if primary in ['very_dark', 'dark']:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # === BƯỚC 5: Non-local Means Denoising ===
        denoise_h, denoise_template, denoise_search, denoise_strength = strategy['denoise']
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        gray_bgr = cv2.fastNlMeansDenoisingColored(gray_bgr, None, denoise_h, denoise_template, denoise_search, denoise_strength)
        gray = cv2.cvtColor(gray_bgr, cv2.COLOR_BGR2GRAY)
        
        # === BƯỚC 6: Edge Enhancement ===
        if metrics['laplacian_var'] > 80:
            blur_enh = cv2.GaussianBlur(gray, (3, 3), 0)
            gray = cv2.addWeighted(gray, 1.2, blur_enh, -0.2, 0)
            gray = np.clip(gray, 0, 255).astype(np.uint8)
        
        enhanced = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        img_tensor = torch.from_numpy(enhanced).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        
        return img_tensor, enhanced, (new_h, new_w)
