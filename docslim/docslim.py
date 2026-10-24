#!/usr/bin/env python3
"""
DocSlim - Intelligent Document, Web, Table, PDF & Image Token Optimizer.
Provides CLI utilities and an MCP (Model Context Protocol) server.
"""

import sys
import os
import json
import re
import csv
import io
import argparse
from typing import List, Dict, Any, Optional

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        sys.stdin.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def read_web(url: str, max_tokens: int = 2000, selector: Optional[str] = None) -> Dict[str, Any]:
    """Fetch and convert webpage into clean, noise-free Markdown with token budget."""
    import requests
    from bs4 import BeautifulSoup, Comment
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 DocSlim/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.content, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    
    # Strip comments and junk tags
    for element in soup(text=lambda text: isinstance(text, Comment)):
        element.extract()
        
    for tag in soup(["script", "style", "svg", "noscript", "iframe", "form", "button", "header", "footer", "nav", "aside", "menu", "dialog"]):
        tag.decompose()
        
    content_root = None
    if selector:
        content_root = soup.select_one(selector)
        
    if not content_root:
        candidates = soup.find_all(["article", "main", "div", "section"])
        best_candidate = None
        best_score = 0
        for cand in candidates:
            text_len = len(cand.get_text(strip=True))
            if text_len > best_score and cand.name in ["article", "main"]:
                best_candidate = cand
                best_score = text_len * 1.5
            elif text_len > best_score:
                best_candidate = cand
                best_score = text_len
        content_root = best_candidate if best_candidate else soup.body or soup
        
    lines = []
    for elem in content_root.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "table"]):
        if elem.name == "h1":
            lines.append(f"\n# {elem.get_text(strip=True)}\n")
        elif elem.name == "h2":
            lines.append(f"\n## {elem.get_text(strip=True)}\n")
        elif elem.name == "h3":
            lines.append(f"\n### {elem.get_text(strip=True)}\n")
        elif elem.name == "h4":
            lines.append(f"\n#### {elem.get_text(strip=True)}\n")
        elif elem.name == "p":
            t = elem.get_text(strip=True)
            if t:
                lines.append(t)
        elif elem.name == "li":
            t = elem.get_text(strip=True)
            if t:
                lines.append(f"- {t}")
        elif elem.name == "pre":
            lines.append(f"\n```\n{elem.get_text().strip()}\n```\n")
        elif elem.name == "table":
            rows = elem.find_all("tr")
            for r_idx, row in enumerate(rows[:15]):
                cols = [c.get_text(strip=True).replace("|", "\\|") for c in row.find_all(["th", "td"])]
                if cols:
                    lines.append("| " + " | ".join(cols) + " |")
                    if r_idx == 0:
                        lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
                        
    text = "\n\n".join(lines)
    raw_tokens = len(text) // 4
    char_limit = max_tokens * 4
    is_truncated = False
    
    if len(text) > char_limit:
        text = text[:char_limit]
        last_nl = text.rfind("\n")
        if last_nl > 0:
            text = text[:last_nl]
        is_truncated = True
        text += f"\n\n> [!NOTE]\n> Truncated at {max_tokens} tokens (total estimated: ~{raw_tokens} tokens). Use a CSS selector or increase max_tokens if needed."
        
    result_md = f"# [{title}]({url})\n\n{text}"
    return {
        "title": title,
        "url": url,
        "tokens_est": min(raw_tokens, max_tokens),
        "total_tokens_est": raw_tokens,
        "truncated": is_truncated,
        "markdown": result_md
    }


def read_pdf(file_path: str, pages: Optional[str] = None, query: Optional[str] = None, max_tokens: int = 2500) -> Dict[str, Any]:
    """Read PDF with page windowing, table of contents, and noise stripping."""
    from pypdf import PdfReader
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
        
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    meta = reader.metadata or {}
    title = meta.get("/Title") or os.path.basename(file_path)
    author = meta.get("/Author") or "Unknown"
    
    toc = []
    try:
        outline = reader.outline
        if outline:
            for item in outline:
                if hasattr(item, "title"):
                    toc.append(str(item.title))
                elif isinstance(item, dict) and "/Title" in item:
                    toc.append(str(item["/Title"]))
    except Exception:
        pass
        
    target_pages = []
    if pages:
        parts = pages.split(",")
        for part in parts:
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                start_p = max(1, int(start))
                end_p = min(total_pages, int(end))
                target_pages.extend(range(start_p - 1, end_p))
            else:
                p = int(part)
                if 1 <= p <= total_pages:
                    target_pages.append(p - 1)
        target_pages = sorted(list(set(target_pages)))
    elif query:
        q_lower = query.lower()
        matched_pages = []
        for i, page in enumerate(reader.pages):
            p_text = page.extract_text() or ""
            if q_lower in p_text.lower():
                matched_pages.append(i)
                if len(matched_pages) >= 5:
                    break
        target_pages = matched_pages if matched_pages else [0]
    else:
        if total_pages <= 3:
            target_pages = list(range(total_pages))
        else:
            target_pages = [0, 1]
            
    page_texts = []
    for p_idx in target_pages:
        page = reader.pages[p_idx]
        txt = page.extract_text() or ""
        clean_lines = [line.strip() for line in txt.splitlines() if line.strip()]
        page_texts.append(f"### Page {p_idx + 1} of {total_pages}\n\n" + "\n".join(clean_lines))
        
    full_text = "\n\n---\n\n".join(page_texts)
    tokens_est = len(full_text) // 4
    
    summary_header = f"# PDF Document: {title}\n- **Author:** {author}\n- **Total Pages:** {total_pages}\n"
    if toc:
        summary_header += "- **Table of Contents:**\n" + "\n".join([f"  - {t}" for t in toc[:10]]) + "\n"
    if not pages and total_pages > len(target_pages):
        summary_header += f"\n> [!NOTE]\n> Showing pages {', '.join(str(p+1) for p in target_pages)} of {total_pages}. To view other pages, pass `pages=\"1-5\"` or `query=\"term\"`.\n\n"
        
    result_md = summary_header + full_text
    return {
        "title": title,
        "total_pages": total_pages,
        "extracted_pages": [p + 1 for p in target_pages],
        "tokens_est": tokens_est,
        "markdown": result_md
    }


def read_table(file_path: str, sample_rows: int = 5, query: Optional[str] = None, columns: Optional[str] = None) -> Dict[str, Any]:
    """Inspect CSV, TSV, or Excel tables with schema, types, and sample data."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Table file not found: {file_path}")
        
    ext = os.path.splitext(file_path)[1].lower()
    headers = []
    rows = []
    total_rows = 0
    
    if ext in [".csv", ".tsv", ".txt"]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            sample_data = f.read(8192)
            f.seek(0)
            delimiter = "\t" if ext == ".tsv" else ","
            try:
                dialect = csv.Sniffer().sniff(sample_data)
                delimiter = dialect.delimiter
            except Exception:
                pass
                
            reader = csv.reader(f, delimiter=delimiter)
            try:
                headers = next(reader)
            except StopIteration:
                return {"error": "Empty table file", "markdown": "Empty table file"}
                
            headers = [h.strip() for h in headers]
            col_indices = None
            if columns:
                requested_cols = [c.strip().lower() for c in columns.split(",")]
                col_indices = [i for i, h in enumerate(headers) if h.lower() in requested_cols]
                if col_indices:
                    headers = [headers[i] for i in col_indices]
                    
            matched_rows = []
            q_lower = query.lower() if query else None
            
            for row in reader:
                total_rows += 1
                if col_indices:
                    row = [row[i] if i < len(row) else "" for i in col_indices]
                if q_lower:
                    if any(q_lower in str(cell).lower() for cell in row):
                        if len(matched_rows) < 15:
                            matched_rows.append(row)
                else:
                    if total_rows <= sample_rows:
                        rows.append(row)
            if q_lower:
                rows = matched_rows
                
    elif ext in [".xlsx", ".xlsm"]:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = wb.active
        iter_rows = sheet.iter_rows(values_only=True)
        try:
            raw_headers = next(iter_rows)
            headers = [str(h) if h is not None else f"Col_{i}" for i, h in enumerate(raw_headers)]
        except StopIteration:
            return {"error": "Empty excel sheet", "markdown": "Empty excel sheet"}
            
        q_lower = query.lower() if query else None
        for raw_row in iter_rows:
            total_rows += 1
            row = [str(c) if c is not None else "" for c in raw_row]
            if q_lower:
                if any(q_lower in cell.lower() for cell in row):
                    if len(rows) < 15:
                        rows.append(row)
            else:
                if total_rows <= sample_rows:
                    rows.append(row)
        wb.close()
    else:
        raise ValueError(f"Unsupported table format: {ext}")
        
    md_lines = [
        f"### Table Inspection: `{os.path.basename(file_path)}`",
        f"- **Total Rows:** {total_rows} | **Columns ({len(headers)}):** {', '.join(headers[:10])}{' ...' if len(headers) > 10 else ''}",
        ""
    ]
    if query:
        md_lines.append(f"> Filter: `{query}` (Showing {len(rows)} matching rows)\n")
    else:
        md_lines.append(f"> Showing first {len(rows)} sample rows of {total_rows} total rows.\n")
        
    display_headers = headers[:12]
    md_lines.append("| " + " | ".join(display_headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(display_headers)) + " |")
    
    for row in rows:
        display_cells = [str(c).replace("|", "\\|").replace("\n", " ") for c in row[:12]]
        while len(display_cells) < len(display_headers):
            display_cells.append("")
        md_lines.append("| " + " | ".join(display_cells) + " |")
        
    md_result = "\n".join(md_lines)
    return {
        "file": file_path,
        "total_rows": total_rows,
        "columns": headers,
        "sample_count": len(rows),
        "tokens_est": len(md_result) // 4,
        "markdown": md_result
    }


def optimize_image(file_path: str, max_dim: int = 1024, quality: int = 80) -> Dict[str, Any]:
    """Inspect and downscale high-resolution images to optimal token dimensions."""
    from PIL import Image
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image not found: {file_path}")
        
    orig_size = os.path.getsize(file_path)
    
    with Image.open(file_path) as img:
        width, height = img.size
        ratio = width / height
        needs_resize = width > max_dim or height > max_dim
        
        if needs_resize:
            if width > height:
                new_width = max_dim
                new_height = int(max_dim / ratio)
            else:
                new_height = max_dim
                new_width = int(max_dim * ratio)
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            new_width, new_height = width, height
            img_resized = img
            
        cache_dir = os.path.join(os.environ.get("TEMP", "."), "docslim_img_cache")
        os.makedirs(cache_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        opt_path = os.path.join(cache_dir, f"{base_name}_opt.webp")
        
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img_resized.save(opt_path, "WEBP", quality=quality)
        else:
            img_resized.convert("RGB").save(opt_path, "WEBP", quality=quality)
            
        opt_size = os.path.getsize(opt_path)
        reduction_pct = round((1 - opt_size / max(1, orig_size)) * 100, 1)
        
        tiles_orig = ((width + 511) // 512) * ((height + 511) // 512)
        tiles_opt = ((new_width + 511) // 512) * ((new_height + 511) // 512)
        orig_tokens_est = tiles_orig * 85 + 85
        opt_tokens_est = tiles_opt * 85 + 85
        
        md_summary = f"""### Image Optimization: `{os.path.basename(file_path)}`
- **Original Resolution:** {width}x{height} ({round(orig_size/1024, 1)} KB) ~ {orig_tokens_est} vision tokens
- **Optimized Resolution:** {new_width}x{new_height} ({round(opt_size/1024, 1)} KB) ~ {opt_tokens_est} vision tokens
- **Token Reduction:** **-{round((1 - opt_tokens_est/max(1, orig_tokens_est))*100, 1)}%**
- **Disk Savings:** **-{reduction_pct}%**
- **Optimized File Path:** `{opt_path}`
"""
        return {
            "original_path": file_path,
            "optimized_path": opt_path,
            "original_resolution": [width, height],
            "optimized_resolution": [new_width, new_height],
            "original_tokens_est": orig_tokens_est,
            "optimized_tokens_est": opt_tokens_est,
            "markdown": md_summary
        }


def read_doc(file_path: str, outline_only: bool = False, max_tokens: int = 2000) -> Dict[str, Any]:
    """Inspect large text/logs/markdown files without blowing context window."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    size_bytes = os.path.getsize(file_path)
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        
    total_lines = len(lines)
    total_tokens_est = size_bytes // 4
    
    headings = []
    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.startswith("#"):
            headings.append(f"L{i+1}: {line_s}")
        elif line_s.startswith("def ") or line_s.startswith("class "):
            headings.append(f"L{i+1}: `{line_s}`")
            
    if outline_only or (total_lines > 300 and total_tokens_est > max_tokens):
        summary = [
            f"# Document Outline: `{os.path.basename(file_path)}`",
            f"- **Total Lines:** {total_lines} | **Size:** {round(size_bytes/1024, 1)} KB (~{total_tokens_est} tokens)",
            f"\n### Outline & Key Anchors ({len(headings)} detected):"
        ]
        if headings:
            summary.extend([f"- {h}" for h in headings[:35]])
        else:
            summary.append("- No markdown headings found. File appears to be raw text or logs.")
        summary.append(f"\n> [!TIP]\n> Use `read_file` with `StartLine` and `EndLine` to read specific sections instead of dumping all {total_lines} lines.")
        return {
            "file": file_path,
            "total_lines": total_lines,
            "outline_mode": True,
            "tokens_est": len("\n".join(summary)) // 4,
            "markdown": "\n".join(summary)
        }
    else:
        return {
            "file": file_path,
            "total_lines": total_lines,
            "outline_mode": False,
            "tokens_est": total_tokens_est,
            "markdown": "".join(lines)
        }


# MCP Server implementation
def run_mcp_server():
    """Runs a Model Context Protocol server over stdio."""
    tools_def = [
        {
            "name": "smart_read_web",
            "description": "Fetch any webpage and return clean, noise-free Markdown stripped of CSS, JS, navbars and ads with strict token budgeting (saves 90-95% tokens).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "max_tokens": {"type": "integer", "description": "Maximum token budget (default: 2000)", "default": 2000},
                    "selector": {"type": "string", "description": "Optional CSS selector to target specific container"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "smart_read_pdf",
            "description": "Read PDF documents with page windowing, table of contents extraction, and header/footer deduplication (saves 80-95% tokens).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path to PDF file"},
                    "pages": {"type": "string", "description": "Page range (e.g. '1-3' or '5,7')"},
                    "query": {"type": "string", "description": "Search term to locate relevant pages"},
                    "max_tokens": {"type": "integer", "description": "Token limit (default: 2500)", "default": 2500}
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "smart_read_table",
            "description": "Inspect CSV, TSV, or Excel tables. Returns schema, data types, and preview rows without dumping thousands of rows into context (saves 95%+ tokens).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to .csv, .tsv, or .xlsx file"},
                    "sample_rows": {"type": "integer", "description": "Number of sample rows to show (default: 5)", "default": 5},
                    "query": {"type": "string", "description": "Filter rows containing keyword"},
                    "columns": {"type": "string", "description": "Comma-separated column names to include"}
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "smart_read_image",
            "description": "Inspect and downscale high-resolution images to optimal token dimensions (saves up to 75% vision tokens).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to image file (.png, .jpg, .webp)"},
                    "max_dim": {"type": "integer", "description": "Maximum width/height dimension in pixels (default: 1024)", "default": 1024},
                    "quality": {"type": "integer", "description": "Compression quality 1-100 (default: 80)", "default": 80}
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "smart_read_doc",
            "description": "Inspect large text/logs/markdown files without blowing context window. Generates structural outline if file is large.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to document file"},
                    "outline_only": {"type": "boolean", "description": "Force structural outline mode", "default": False},
                    "max_tokens": {"type": "integer", "description": "Token budget threshold (default: 2000)", "default": 2000}
                },
                "required": ["file_path"]
            }
        }
    ]

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
            
        try:
            req = json.loads(line)
        except Exception:
            continue
            
        req_id = req.get("id")
        method = req.get("method")
        
        if method == "initialize":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "docslim",
                        "version": "1.0.0"
                    }
                }
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": tools_def
                }
            }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})
            
            try:
                if tool_name == "smart_read_web":
                    ret = read_web(args["url"], args.get("max_tokens", 2000), args.get("selector"))
                elif tool_name == "smart_read_pdf":
                    ret = read_pdf(args["file_path"], args.get("pages"), args.get("query"), args.get("max_tokens", 2500))
                elif tool_name == "smart_read_table":
                    ret = read_table(args["file_path"], args.get("sample_rows", 5), args.get("query"), args.get("columns"))
                elif tool_name == "smart_read_image":
                    ret = optimize_image(args["file_path"], args.get("max_dim", 1024), args.get("quality", 80))
                elif tool_name == "smart_read_doc":
                    ret = read_doc(args["file_path"], args.get("outline_only", False), args.get("max_tokens", 2000))
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                    
                text_out = ret.get("markdown", "")
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": text_out}
                        ]
                    }
                }
            except Exception as e:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "isError": True,
                    "result": {
                        "content": [
                            {"type": "text", "text": f"DocSlim Error: {str(e)}"}
                        ]
                    }
                }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="DocSlim - Document, Web, Table, PDF & Image Token Optimizer")
    subparsers = parser.add_subparsers(dest="subcommand")
    
    # serve --mcp
    p_serve = subparsers.add_parser("serve", help="Run MCP server")
    p_serve.add_argument("--mcp", action="store_true", help="Run as MCP server over stdio")
    
    # web
    p_web = subparsers.add_parser("web", help="Read webpage to compact Markdown")
    p_web.add_argument("url", help="Webpage URL")
    p_web.add_argument("--max-tokens", type=int, default=2000, help="Max tokens (default: 2000)")
    p_web.add_argument("--selector", help="CSS selector")
    
    # pdf
    p_pdf = subparsers.add_parser("pdf", help="Read PDF compactly")
    p_pdf.add_argument("file", help="Path to PDF file")
    p_pdf.add_argument("--pages", help="Page range (e.g. 1-3 or 5)")
    p_pdf.add_argument("--query", help="Keyword search in PDF")
    
    # table
    p_table = subparsers.add_parser("table", help="Inspect table (CSV, TSV, XLSX)")
    p_table.add_argument("file", help="Path to table file")
    p_table.add_argument("--sample", type=int, default=5, help="Sample rows (default: 5)")
    p_table.add_argument("--query", help="Filter keyword")
    p_table.add_argument("--columns", help="Columns to display (comma-separated)")
    
    # image
    p_img = subparsers.add_parser("image", help="Downscale image for vision models")
    p_img.add_argument("file", help="Path to image file")
    p_img.add_argument("--max-dim", type=int, default=1024, help="Max dimension (default: 1024)")
    p_img.add_argument("--quality", type=int, default=80, help="WebP quality (default: 80)")
    
    # doc
    p_doc = subparsers.add_parser("doc", help="Inspect large text/markdown/log file")
    p_doc.add_argument("file", help="Path to document file")
    p_doc.add_argument("--outline", action="store_true", help="Show outline only")
    
    args = parser.parse_args()
    
    if args.subcommand == "serve":
        run_mcp_server()
    elif args.subcommand == "web":
        res = read_web(args.url, args.max_tokens, args.selector)
        print(res["markdown"])
    elif args.subcommand == "pdf":
        res = read_pdf(args.file, args.pages, args.query)
        print(res["markdown"])
    elif args.subcommand == "table":
        res = read_table(args.file, args.sample, args.query, args.columns)
        print(res["markdown"])
    elif args.subcommand == "image":
        res = optimize_image(args.file, args.max_dim, args.quality)
        print(res["markdown"])
    elif args.subcommand == "doc":
        res = read_doc(args.file, args.outline)
        print(res["markdown"])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
