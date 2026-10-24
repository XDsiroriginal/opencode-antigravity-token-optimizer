"""
Comprehensive Verification and Test Suite for DocSlim Token Optimizer.
Tests: Web, PDF, Table, Image, Large Doc, and MCP Server Protocol.
"""

import os
import sys
import json
import subprocess

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image, ImageDraw


def test_web():
    print("--- 1. Testing Web Scraper & Readability ---")
    cmd = ["docslim.cmd", "web", "https://example.com"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(f"Exit code: {p.returncode}")
    assert p.returncode == 0
    assert "Example Domain" in p.stdout
    print("✓ Web extraction passed!\n")


def test_table():
    print("--- 2. Testing Table (CSV) Analyzer ---")
    test_csv = os.path.join(os.environ["TEMP"], "test_data.csv")
    with open(test_csv, "w", encoding="utf-8") as f:
        f.write("id,name,department,salary\n")
        for i in range(1, 201):
            f.write(f"{i},Employee_{i},{'Engineering' if i % 2 == 0 else 'Marketing'},{50000 + i * 100}\n")
            
    # Sample mode
    cmd = ["docslim.cmd", "table", test_csv, "--sample", "3"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(f"Exit code: {p.returncode}")
    assert p.returncode == 0
    assert "Total Rows" in p.stdout and "200" in p.stdout
    assert "Employee_1" in p.stdout
    
    # Query mode
    cmd_query = ["docslim.cmd", "table", test_csv, "--query", "Employee_42"]
    p_q = subprocess.run(cmd_query, capture_output=True, text=True, encoding="utf-8")
    assert "Employee_42" in p_q.stdout
    print("✓ Table analyzer passed!\n")


def test_pdf():
    print("--- 3. Testing PDF Smart Reader ---")
    test_pdf_path = os.path.join(os.environ["TEMP"], "test_report.pdf")
    c = canvas.Canvas(test_pdf_path, pagesize=letter)
    
    # Page 1: Cover
    c.setTitle("Annual System Architecture Report")
    c.setAuthor("DevOps Engineering Team")
    c.drawString(100, 700, "Annual System Architecture Report 2026")
    c.drawString(100, 680, "Executive Summary: Cloud infrastructure token consumption.")
    c.showPage()
    
    # Page 2: Token Details
    c.drawString(100, 700, "Section 2: High Performance Optimizations")
    c.drawString(100, 680, "Critical findings: RTK reduces 85% bash output, CodeGraph reduces 60% queries.")
    c.showPage()
    
    # Page 3: Secret Keyword
    c.drawString(100, 700, "Section 3: Database Benchmarks")
    c.drawString(100, 680, "Benchmark keyword: QUANTUM_OPTIMIZER_777 achieved 10x throughput.")
    c.showPage()
    c.save()
    
    # Test reading page 2
    cmd = ["docslim.cmd", "pdf", test_pdf_path, "--pages", "2"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0
    assert "Page 2 of 3" in p.stdout
    assert "High Performance Optimizations" in p.stdout
    
    # Test searching keyword
    cmd_q = ["docslim.cmd", "pdf", test_pdf_path, "--query", "QUANTUM_OPTIMIZER_777"]
    p_q = subprocess.run(cmd_q, capture_output=True, text=True, encoding="utf-8")
    assert p_q.returncode == 0
    assert "QUANTUM_OPTIMIZER_777" in p_q.stdout
    print("✓ PDF reader passed!\n")


def test_image():
    print("--- 4. Testing Image Downscaling & Vision Token Optimizer ---")
    test_img_path = os.path.join(os.environ["TEMP"], "huge_screenshot.png")
    # Create 3840x2160 4K image
    img = Image.new("RGB", (3840, 2160), color=(30, 40, 50))
    d = ImageDraw.Draw(img)
    d.text((100, 100), "4K Ultra-HD Application Dashboard", fill=(255, 255, 255))
    img.save(test_img_path, "PNG")
    
    cmd = ["docslim.cmd", "image", test_img_path, "--max-dim", "1024"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(f"Exit code: {p.returncode}")
    assert p.returncode == 0
    assert "Original Resolution" in p.stdout and "3840x2160" in p.stdout
    assert "Optimized Resolution" in p.stdout and "1024x576" in p.stdout
    assert "Token Reduction" in p.stdout
    print("✓ Image optimizer passed!\n")


def test_doc():
    print("--- 5. Testing Large Document Outline ---")
    test_doc_path = os.path.join(os.environ["TEMP"], "big_spec.md")
    with open(test_doc_path, "w", encoding="utf-8") as f:
        f.write("# Specification 1.0\n\nIntro text...\n\n")
        for i in range(1, 50):
            f.write(f"## Module {i}: Architecture and Performance\n")
            f.write(f"Detailed documentation for module {i} with boilerplate...\n" * 15)
            
    cmd = ["docslim.cmd", "doc", test_doc_path, "--outline"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0
    assert "Document Outline" in p.stdout
    assert "Module 1:" in p.stdout
    assert "Module 2:" in p.stdout
    print("✓ Document outline passed!\n")


def test_mcp_protocol():
    print("--- 6. Testing MCP Server Protocol over stdio ---")
    proc = subprocess.Popen(
        ["docslim.cmd", "serve", "--mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    
    # 1. Initialize
    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    init_res = json.loads(proc.stdout.readline())
    assert init_res.get("id") == 1
    assert init_res["result"]["serverInfo"]["name"] == "docslim"
    
    # 2. Tools list
    list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    proc.stdin.write(json.dumps(list_req) + "\n")
    proc.stdin.flush()
    list_res = json.loads(proc.stdout.readline())
    tools = [t["name"] for t in list_res["result"]["tools"]]
    assert "smart_read_web" in tools
    assert "smart_read_pdf" in tools
    assert "smart_read_table" in tools
    assert "smart_read_image" in tools
    assert "smart_read_doc" in tools
    
    # 3. Call tool
    test_csv = os.path.join(os.environ["TEMP"], "test_data.csv")
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "smart_read_table",
            "arguments": {"file_path": test_csv, "sample_rows": 2}
        }
    }
    proc.stdin.write(json.dumps(call_req) + "\n")
    proc.stdin.flush()
    call_res = json.loads(proc.stdout.readline())
    assert call_res.get("id") == 3
    content_text = call_res["result"]["content"][0]["text"]
    assert "Table Inspection" in content_text
    
    proc.kill()
    print("✓ MCP Server stdio protocol passed!\n")


if __name__ == "__main__":
    test_web()
    test_table()
    test_pdf()
    test_image()
    test_doc()
    test_mcp_protocol()
    print("========================================")
    print("ALL 6 DOCSLIM MODULE TESTS PASSED 100%!")
    print("========================================")
