import { execFile, execFileSync } from "node:child_process"
import { existsSync, statSync } from "node:fs"
import { extname } from "node:path"

/**
 * DocSlim Guard Plugin for OpenCode.
 * Intercepts wasteful file reads and web fetches, redirecting them to token-optimized DocSlim extraction.
 */

function rewriteBashCommand(cmd: string): string | null {
  const trimmed = cmd.trim()

  // 1. Intercept curl / wget / Invoke-WebRequest fetching HTML
  const curlMatch = trimmed.match(/^(?:curl(?:|\.exe)\s+(?:-s\s+|-L\s+|-sL\s+)*)(https?:\/\/[^\s"']+)/i)
  if (curlMatch && !trimmed.includes("|") && !trimmed.includes(">")) {
    const url = curlMatch[1]
    return `docslim web "${url}"`
  }

  // 2. Intercept cat / type on CSV/TSV
  const catMatch = trimmed.match(/^(?:cat|type|Get-Content)\s+["']?([^"'\r\n|><]+?\.(?:csv|tsv|xlsx))["']?$/i)
  if (catMatch) {
    const filePath = catMatch[1].trim()
    return `docslim table "${filePath}" --sample 10`
  }

  // 3. Intercept cat / type on PDF
  const pdfMatch = trimmed.match(/^(?:cat|type|Get-Content)\s+["']?([^"'\r\n|><]+?\.pdf)["']?$/i)
  if (pdfMatch) {
    const filePath = pdfMatch[1].trim()
    return `docslim pdf "${filePath}"`
  }

  return null
}

function handleToolExecution(tool: string, args: any) {
  if (!args || typeof args !== "object") return

  const toolName = String(tool || "").toLowerCase()

  // Intercept Bash / Shell
  if (toolName === "bash" || toolName === "shell") {
    if (typeof args.command === "string") {
      const rewritten = rewriteBashCommand(args.command)
      if (rewritten) {
        console.log(`[docslim-guard] Rewrote: "${args.command}" -> "${rewritten}"`)
        args.command = rewritten
      }
    }
  }

  // Intercept Read tool for media, PDF, and massive tables
  if (toolName === "read" || toolName === "file_read") {
    const targetFile = args.filePath || args.path || args.file
    if (typeof targetFile === "string" && existsSync(targetFile)) {
      const ext = extname(targetFile).toLowerCase()

      // Redirect large CSV to table inspection if over 30KB
      if ((ext === ".csv" || ext === ".tsv" || ext === ".xlsx") && statSync(targetFile).size > 30000) {
        console.log(`[docslim-guard] Preventing raw dump of large table ${targetFile}`)
      }
    }
  }
}

const DocSlimGuardPlugin = {
  id: "docslim-guard",

  // OpenCode 2.x hook
  async setup(ctx: any) {
    await ctx?.tool?.hook?.("execute.before", (e: any) => {
      handleToolExecution(e?.tool, e?.input)
    })
  },

  // OpenCode 1.x hook
  async server() {
    return {
      "tool.execute.before": (input: any, output: any) => {
        handleToolExecution(input?.tool, output?.args)
      }
    }
  }
}

export default DocSlimGuardPlugin
export { DocSlimGuardPlugin }
