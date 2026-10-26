# Token Optimization & High Performance Guidelines

This block is installed by the pack. It is always active.

## Mandatory tool routing

- **Web pages & URLs**: never dump raw HTML with `curl` / `Invoke-WebRequest`. Use the
  `smart_read_web` MCP tool, or `docslim web <url>` in the terminal. It returns clean
  Markdown without scripts, CSS, navigation or ads (saves 90-95% tokens).
- **PDF documents**: never paste a whole PDF into context. Use `smart_read_pdf` with a
  page range or a query, or `docslim pdf <file> --pages <range>`.
- **Tables (CSV / TSV / XLSX)**: never read a whole table. Use `smart_read_table`, or
  `docslim table <file> --sample <N> --query <term>`. It returns schema, row count and
  a preview (saves 95%+ tokens).
- **Images & screenshots**: use `smart_read_image` (or `docslim image <file>`) to
  downscale to optimal vision resolution before analysis.
- **Large text / logs / markdown**: use `smart_read_doc` instead of reading a huge file
  line by line.
- **Terminal output**: when the `rtk` PreToolUse hook is active, shell output is condensed.
  Treat a condensed result as complete; do not re-run the command in verbose form. If a
  result is clearly unusable (empty, garbled, or contradicting its exit code), re-run it
  with `RTK_DISABLED=1` in front of the command.

## Context discipline

- **Surgical context retrieval**: when reading large files, always specify line bounds
  (`StartLine` / `EndLine`) instead of dumping the entire file into the context window.
- **Compact edits**: use targeted `edit_file` calls with minimal contiguous hunks. Never
  reproduce hundreds of lines of unchanged code.
- **Terse communication**: no filler, no restating untouched files, no repeating diffs.
- **Batch related commands** into one call to save turns.
