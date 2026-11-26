# PowerShell Snippets

Snippets for PowerShell scripts: `powershell.json` for `.ps1` files.

In LightLine, type a prefix and press `Ctrl+Space`, then `Tab` to move between the placeholders.

| Scripts and functions | Control flow | Data and pipelines |
| --- | --- | --- |
| `script` (param block, strict mode, stop on errors) | `if`, `ife`, `switch` | `hash` (`[ordered]@{}`), `pscustom` (`[PSCustomObject]@{}`) |
| `func`, `afunc` (`[CmdletBinding()]` with a pipeline parameter) | `foreach`, `for`, `while`, `do` | `splat` (splatting), `fe` (`ForEach-Object`), `where` (`Where-Object`) |
| `param`, `help` (comment-based help) | `try` (catch and finally) | `class`, `enum`, `here` (here-string) |
| `region`, `describe` (Pester test) | `lines` (each line of a file) | `mkdir` (create a folder if it's missing) |
