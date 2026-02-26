
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from extract_app.core.settings_manager import SettingsManager
from extract_app.core.translation_service import TranslationService
from extract_app.core.local_genai import LocalGenAI

def test_integration():
    print("=== Testing Local Translation Integration ===")
    
    # 1. Setup Settings
    settings_path = "user_data/test_settings.json"
    mgr = SettingsManager(settings_path)
    
    model_path = r"C:\Users\AORUS\Documents\Projects\translategemma-12b-it\gemma-2-9b-it-Q4_K_M.gguf"
    
    print(f"Configuring settings...")
    mgr.set("translation_engine", "local")
    mgr.set("local_model_path", model_path)
    mgr.set("n_gpu_layers", -1) # GPU
    mgr.set("current_style", "standard")
    
    # 2. Init Service
    print("Initializing Translation Service...")
    service = TranslationService(mgr)
    
    # Check if LocalGenAI singleton is clean
    # LocalGenAI.get_instance().unload_model()
    
    # 3. Translate
    text = "Artificial Intelligence is transforming the world rapidly. It brings both opportunities and challenges."
    print(f"\n[Input]: {text}")
    print("[Translating]... (First run may take time to load model)")
    
    import time
    start = time.time()
    result = service.translate_text(text)
    end = time.time()
    
    print(f"\n[Result]: {result}")
    print(f"[Time]: {end - start:.2f}s")
    
    if result and "Trí tuệ nhân tạo" in result or "AI" in result:
        print("\nSUCCESS: Translation logic works correctly!")
        return True
    else:
        print("\nFAILURE: Translation returned empty or unexpected result.")
        return False

if __name__ == "__main__":
    try:
        if test_integration():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
