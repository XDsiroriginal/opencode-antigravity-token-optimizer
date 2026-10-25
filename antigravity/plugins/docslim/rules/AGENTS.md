# DocSlim Token Reduction Rules

When reading external data:
- Use `smart_read_web` instead of curl/fetch to strip HTML scripts, CSS, and navigation headers.
- Use `smart_read_pdf` with targeted pages instead of dumping entire PDFs into context.
- Use `smart_read_table` for CSV, TSV, and Excel files to inspect schema and sample rows.
- Use `smart_read_image` to downscale high-resolution images for vision models.
