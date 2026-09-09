import torch
import sys
import platform

def check_gpu():
    print("=" * 50)
    print("GPU VERIFICATION REPORT")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print()

    if 'torch' in sys.modules:
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA runtime version: {torch.version.cuda}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"GPU name: {torch.cuda.get_device_name(0)}")
            print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            print("GPU: NOT AVAILABLE")
    else:
        print("PyTorch not installed")

    print("=" * 50)

if __name__ == "__main__":
    check_gpu()