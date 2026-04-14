"""
Check GPU availability for PyTorch
"""
import torch
import sys

print("=" * 80)
print("GPU AVAILABILITY CHECK")
print("=" * 80)

print(f"\nPyTorch version: {torch.__version__}")
print(f"Python version: {sys.version}")

print("\n" + "=" * 80)
print("CUDA STATUS")
print("=" * 80)

cuda_available = torch.cuda.is_available()
print(f"\nCUDA available: {cuda_available}")

if cuda_available:
    print(f"CUDA version: {torch.version.cuda}")
    print(f"cuDNN version: {torch.backends.cudnn.version()}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    
    print("\n" + "=" * 80)
    print("GPU DETAILS")
    print("=" * 80)
    
    for i in range(torch.cuda.device_count()):
        print(f"\nGPU {i}:")
        print(f"  Name: {torch.cuda.get_device_name(i)}")
        print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
        print(f"  Compute Capability: {torch.cuda.get_device_properties(i).major}.{torch.cuda.get_device_properties(i).minor}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("\n✅ GPU is available! BERT training will be FAST (5-10 minutes)")
    print("   Use: python train_bert.py --model distilbert-base-uncased --epochs 3")
    
else:
    print(f"CUDA version: Not available")
    print(f"Number of GPUs: 0")
    
    print("\n" + "=" * 80)
    print("WHY NO GPU?")
    print("=" * 80)
    
    print("\nPossible reasons:")
    print("1. No NVIDIA GPU in your system")
    print("2. PyTorch CPU-only version installed")
    print("3. CUDA drivers not installed")
    
    print("\n" + "=" * 80)
    print("CHECK YOUR SYSTEM")
    print("=" * 80)
    
    print("\nTo check if you have an NVIDIA GPU:")
    print("  Run: nvidia-smi")
    print("  Or check Device Manager → Display adapters")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("\n⚠️  No GPU detected - BERT training will be SLOW (30-60 minutes)")
    print("   Options:")
    print("   1. Use CPU (slow): python train_bert.py --model distilbert-base-uncased --epochs 3 --device cpu")
    print("   2. Install PyTorch with CUDA if you have NVIDIA GPU")
    print("   3. Use XGBoost instead (fast on CPU): Already trained with 86.85% accuracy!")

print("\n" + "=" * 80)
