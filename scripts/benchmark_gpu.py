
import time
import sys
import os
from llama_cpp import Llama

def run_benchmark(model_path, n_gpu_layers, label):
    print(f"\n{'='*50}")
    print(f"Running Benchmark: {label}")
    print(f"Model: {os.path.basename(model_path)}")
    print(f"n_gpu_layers: {n_gpu_layers}")
    print(f"{'='*50}")

    try:
        # Load model
        start_load = time.time()
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=2048,
            verbose=True # ENABLED VERBOSE LOGGING
        )
        load_time = time.time() - start_load
        print(f"Model loaded in {load_time:.2f} seconds.")

        # Run inference
        prompt = "Write a short poem about the future of artificial intelligence."
        print(f"\nGenerating response for prompt: '{prompt}'...\n")
        
        start_gen = time.time()
        output = llm(
            prompt,
            max_tokens=100,
            stop=["\n"],
            echo=True
        )
        end_gen = time.time()

        # Calculate metrics
        usage = output['usage']
        total_tokens = usage['total_tokens']
        gen_time = end_gen - start_gen
        tokens_per_sec = total_tokens / gen_time

        print(f"\nResponse: {output['choices'][0]['text'].strip()}")
        print(f"\nMetrics for {label}:")
        print(f"  - Total Tokens: {total_tokens}")
        print(f"  - Total Time:   {gen_time:.2f} s")
        print(f"  - Speed:        {tokens_per_sec:.2f} tokens/sec")
        
        return tokens_per_sec

    except Exception as e:
        print(f"Error running benchmark: {e}")
        return 0

def main():
    print("PDF/EPUB Extractor - GPU Benchmark Tool")
    print("---------------------------------------")

    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        print("\nNo model path provided.")
        model_path = input("Enter the absolute path to your .gguf model file: ").strip().strip('"')

    if not os.path.exists(model_path):
        print(f"Error: File not found at {model_path}")
        return

    # 1. Run CPU Benchmark
    print("\n[1/2] Starting CPU Benchmark (n_gpu_layers=0)...")
    cpu_speed = run_benchmark(model_path, n_gpu_layers=0, label="CPU ONLY")

    # 2. Run GPU Benchmark
    print("\n[2/2] Starting GPU Benchmark (n_gpu_layers=-1)...")
    gpu_speed = run_benchmark(model_path, n_gpu_layers=-1, label="GPU (CUDA)")

    # Summary
    print(f"\n{'='*50}")
    print("BENCHMARK RESULTS")
    print(f"{'='*50}")
    print(f"CPU Speed: {cpu_speed:.2f} t/s")
    print(f"GPU Speed: {gpu_speed:.2f} t/s")
    
    if cpu_speed > 0:
        speedup = gpu_speed / cpu_speed
        print(f"\nSpeedup: {speedup:.2f}x")
        if speedup > 1.5:
            print("Conclusion: GPU acceleration is WORKING correctly! 🚀")
        elif speedup > 0.9:
            print("Conclusion: GPU speed is similar to CPU. Check if model fits in VRAM.")
        else:
            print("Conclusion: GPU is SLOWER. Something might be wrong configuration.")
    else:
        print("Could not calculate speedup due to CPU error.")

if __name__ == "__main__":
    main()
