# Contributing

Thank you for helping. Each extension here is a folder of plain data files: nothing in this repository runs code inside LightLine.

## Adding an extension

1. Copy `template/color-theme` to `themes/lightline-<name>/`, or `template/snippets` to `snippets/lightline-<name>/`.
2. Set `id` in its `extension.toml` to the folder's name, and write a `name` and a `description` of at most 60 characters (LightLine's Extensions panel cuts off a longer one).
3. Run `python scripts/check.py` (Python 3.11 or later, nothing to install) and fix what it lists.
4. Try it in LightLine. Copy the folder into `%APPDATA%\LightLine\extensions\`, restart LightLine, and use it.
5. Open a pull request with a screenshot.

## Changing an extension

Bump `version` in its `extension.toml`: `x.y.z`, with the last number for fixes, the middle one for additions, and the first one for anything that changes what users already rely on.

A merged change doesn't reach users by itself. LightLine installs each extension at the commit [LightLine's list](https://github.com/mehmoodulhaq570/LightLine/blob/main/registry/extensions.toml) pins, so a pull request to LightLine moves that commit. LightLine fetches its list when the Extensions panel opens, so that doesn't need a LightLine release.

## What's checked

`scripts/check.py` runs on every push and pull request.

**Every extension:**
- `extension.toml` parses.
- The id is `lightline-…`, matches its folder and isn't used twice.
- The version is `x.y.z`.
- The description fits in 60 characters.
- `repository` points here.

**Color themes:**
- Each variant's name starts with `LightLine `, and it sets an `appearance` and every key LightLine reads.
- Text and syntax colors are opaque, and stand out from the background by at least **4.5:1**, or **7:1** for a variant whose name ends in ` Contrast`.
- They also stand out from the caret line by at least 4.5:1.
- Line numbers need 3:1.

**Snippets:**
- Every file named in `snippets = [...]` exists and is valid JSON.
- Every snippet has a prefix, a body and a description.
- No prefix is used twice in a file, and every `${` is closed.
- No tab stop is used twice. LightLine doesn't mirror a repeated tab stop, so the second one would come out empty; write the text again instead.
- There are no variables such as `$TM_FILENAME`, which LightLine leaves empty.

## What gets reviewed

- It works in the latest LightLine release.
- Snippets are indented with `\t`, which LightLine turns into the file's own indentation, and end at `$0`.
- Themes look right in the whole window, not only the editor: the sidebar, tabs, status bar, terminal and Problems panel.
- Everything in it is yours to share under the MIT license.
