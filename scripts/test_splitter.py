# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: scripts/test_splitter.py
# Version: 1.0.0
# Author: Antigravity
# Description: Verifies SmartSplitter logic.
# --------------------------------------------------------------------------------

import sys
import os
from bs4 import BeautifulSoup

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from extract_app.core.content_structurer import SmartSplitter
    
    html_sample = """
    <html>
    <body>
        <p>Introduction text.</p>
        
        <h2>Chapter 1: The Beginning</h2>
        <p>Para 1</p>
        <img src="img1.jpg"/>
        <p>Para 2</p>
        
        <h3>Section 1.1: Early Days</h3>
        <p>Para 3</p>
        
        <h2>Chapter 2: The End</h2>
        <p>Para 4</p>
    </body>
    </html>
    """
    
    print("Testing SmartSplitter.split_soup_to_sections...")
    soup = BeautifulSoup(html_sample, 'html.parser')
    sections = SmartSplitter.split_soup_to_sections(soup)
    
    # Expect 4 sections:
    # 1. "Nội dung" (Intro)
    # 2. "Chapter 1: The Beginning"
    # 3. "Section 1.1: Early Days"
    # 4. "Chapter 2: The End"
    
    print(f"Found {len(sections)} sections.")
    for idx, sec in enumerate(sections):
        print(f"[{idx}] {sec['subtitle']} - Tags: {len(sec['tags'])}")
        
    assert len(sections) == 4
    assert sections[0]['subtitle'] == "Nội dung"
    assert sections[1]['subtitle'] == "Chapter 1: The Beginning"
    assert sections[2]['subtitle'] == "Section 1.1: Early Days"
    assert sections[3]['subtitle'] == "Chapter 2: The End"
    
    print("ALL TESTS PASSED.")

except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
