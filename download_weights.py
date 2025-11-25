import os
import gdown
import sys

def download_weights():
    """Download model weights from Google Drive if not exists"""
    
    weights_dir = "app/weights"
    os.makedirs(weights_dir, exist_ok=True)
    
    dbnet_path = os.path.join(weights_dir, "model_best_100_03.pth")
    if not os.path.exists(dbnet_path):
        print("📥 Downloading DBNet weights...")
        dbnet_url = "https://drive.google.com/uc?id=18ZQ19qpJKCK8ScW2C2zOxJhXwpAqzGhh"
        gdown.download(dbnet_url, dbnet_path, quiet=False)
        print("⚠️  Please upload DBNet weights to Google Drive and update URL")
    
    vietocr_path = os.path.join(weights_dir, "mymodelOCR.pth")
    if not os.path.exists(vietocr_path):
        print("📥 Downloading VietOCR weights...")
        vietocr_url = "https://drive.google.com/uc?id=1c8iZ-6lNHiQW8poo5KmzdkYum-8Bj73q"
        gdown.download(vietocr_url, vietocr_path, quiet=False)
        print("⚠️  Please upload VietOCR weights to Google Drive and update URL")
    
    print("✅ All weights ready!")

if __name__ == "__main__":
    download_weights()
