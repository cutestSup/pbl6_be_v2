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
        dbnet_url = "https://drive.google.com/uc?id=1Wz-cZvZkY4Rv-9y3vT3YIe23bXhS3myq"
        gdown.download(dbnet_url, dbnet_path, quiet=False)
    
    vietocr_path = os.path.join(weights_dir, "mymodelOCR.pth")
    if not os.path.exists(vietocr_path):
        print("📥 Downloading VietOCR weights...")
        vietocr_url = "https://drive.google.com/uc?id=1AyhUYbFIdP_rL4PD0zmfpa1RzPKPwW5T"
        gdown.download(vietocr_url, vietocr_path, quiet=False)
    
    print("✅ All weights ready!")

if __name__ == "__main__":
    download_weights()
