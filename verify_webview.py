
import os
import sys
from pathlib import Path
import shutil

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), "src"))

from extract_app.core.webview_generator import generate_webview

def test_webview_markdown():
    print("--- Testing Webview Markdown Generation ---")
    
    # Mock Data
    chapters = [{
        "title": "Chapter 1",
        "articles": [{
            "subtitle": "Test Article",
            "content_text": """# Heading 1
This is a paragraph.

## Heading 2
- Item 1
- Item 2

**Bold text** and *italic text*.

[Image: test.jpg]""",
            "translation_text": """# Tiêu đề 1
Đây là đoạn văn.

## Tiêu đề 2
- Mục 1
- Mục 2

**In đậm** và *in nghiêng*."""
        }]
    }]
    
    output_dir = Path("test_webview_output")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()
    
    try:
        generate_webview("Test Book", "Author", chapters, output_dir)
        
        # Check JS content for regex logic presence
        js_path = output_dir / "webview" / "js" / "app.js"
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()
            
            # Check for key logic parts
            checks = [
                ("processContent", "Function definition"),
                ("Markdown Lines processing", "Markdown comment"),
                ("replace(/\*\*(.*?)\*\*/g", "Bold regex"),
                ("replace(/\*(.*?)\*/g", "Italic regex"),
                ("<p>${block}</p>", "Paragraph wrapping")
            ]
            
            print("\nChecking generated JS logic:")
            for check, desc in checks:
                if check in content or check.replace("\\", "") in content:
                    print(f"✅ Found {desc}")
                else:
                    print(f"❌ Missing {desc}")
                    
        print("\n✅ Webview generation successful.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_webview_markdown()
