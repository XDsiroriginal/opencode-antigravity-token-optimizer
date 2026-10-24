# Token Optimization & High Performance Guidelines

- **Surgical Context Retrieval**: When reading large files, always specify line bounds (`StartLine` and `EndLine`) instead of dumping entire files into the context window.
- **Semantic Codebase Exploration**: Use CodeGraph MCP tools (`codegraph_explore`) to jump directly to symbols, call graphs, and definitions instead of multi-turn brute-force grep loops.
- **Web Pages & URLs**: NEVER use `curl` or raw HTTP GET to dump HTML into the prompt. Use `smart_read_web` MCP tool or `docslim web <url>`. It converts HTML to clean, noise-free Markdown, stripping scripts, styles, and navigation (saves 90-95% tokens).
- **PDF Documents**: NEVER dump entire raw PDFs into context. Use `smart_read_pdf` MCP tool or `docslim pdf <file> --pages <range>`. It extracts TOC and page windows with running headers/footers removed.
- **Tables & Tabular Data (CSV/TSV/XLSX)**: NEVER read massive CSVs directly into the context window. Use `smart_read_table` MCP tool or `docslim table <file> --sample <N> --query <term>`. It extracts schema, row count, and preview rows (saves 95%+ tokens).
- **Images & Vision**: When inspecting high-resolution screenshots or photos, use `smart_read_image` MCP tool or `docslim image <file>` to downscale to optimal vision resolution (saves up to 75% vision tokens).
- **Compact Edits**: Use targeted `edit_file` calls for minimal contiguous hunks. Do not reproduce hundreds of lines of unchanged code.
- **Condensed Command Output**: Terminal outputs are intercepted and compressed by RTK. Treat condensed outputs as complete results; do not re-run verbose commands unless output was explicitly garbled.
- **Terse and Direct Communication**: Avoid unnecessary conversational filler, boilerplate summaries of untouched files, or redundant restatements of code diffs.
