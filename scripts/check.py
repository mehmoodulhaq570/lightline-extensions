"""Checks every extension in this repository before it can be merged.

Run from the repository root: python scripts/check.py
Uses only Python's standard library (3.11 or later, for tomllib).
Exits with 1 and lists every problem when anything is wrong.
"""

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "https://github.com/mehmoodulhaq570/lightline-extensions"
KINDS = {"themes": "color-theme", "snippets": "snippets"}
# LightLine's Extensions panel cuts a longer description off.
DESCRIPTION_LIMIT = 60
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
COLOR = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")

# The theme keys LightLine reads (color_theme_adapter.rs). Every variant sets
# all of them, so it looks the same in LightLine as in its preview.
STYLE_KEYS = [
    "background", "editor.background", "editor.foreground", "text", "text.muted",
    "text.placeholder", "text.accent", "border", "border.variant", "border.focused",
    "status_bar.background", "tab_bar.background", "element.hover",
    "panel.background", "editor.active_line.background", "editor.line_number",
    "editor.active_line_number", "error", "warning", "info", "terminal.background",
    "terminal.foreground",
] + [
    f"terminal.ansi.{bright}{name}"
    for bright in ("", "bright_")
    for name in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
]
SYNTAX_KEYS = [
    "comment", "string", "keyword", "type", "number", "preproc", "function",
    "operator", "attribute", "punctuation",
]
# Colors that are read as text, so they must stand out from the background.
TEXT_KEYS = ["text", "text.muted", "error", "warning", "editor.active_line_number"]

problems: list[str] = []


def problem(where: Path | str, message: str) -> None:
    where = where.relative_to(ROOT).as_posix() if isinstance(where, Path) else where
    problems.append(f"{where}: {message}")


def luminance(color: str) -> float:
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def opaque(color: str) -> bool:
    return len(color) == 7 or color[7:].lower() == "ff"


def check_manifest(folder: Path, template: bool) -> dict | None:
    path = folder / "extension.toml"
    try:
        manifest = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problem(folder, "has no extension.toml")
        return None
    except tomllib.TOMLDecodeError as error:
        problem(path, f"doesn't parse: {error}")
        return None
    for key in ("id", "name", "version", "schema_version", "authors", "description", "repository"):
        if key not in manifest:
            problem(path, f"needs {key}")
    ident = str(manifest.get("id", ""))
    if not re.fullmatch(r"lightline-[a-z0-9]+(-[a-z0-9]+)*", ident):
        problem(path, "id must be lightline- then lowercase words joined by -")
    if not template and ident != folder.name:
        problem(path, f"id {ident!r} must be the folder's name, {folder.name!r}")
    if not VERSION.match(str(manifest.get("version", ""))):
        problem(path, "version must be x.y.z")
    if manifest.get("schema_version") != 1:
        problem(path, "schema_version must be 1")
    description = str(manifest.get("description", ""))
    if len(description) > DESCRIPTION_LIMIT:
        problem(path, f"description is longer than {DESCRIPTION_LIMIT} characters")
    if manifest.get("repository") != REPOSITORY:
        problem(path, f"repository must be {REPOSITORY}")
    return manifest


def check_theme(folder: Path) -> None:
    files = sorted((folder / "themes").glob("*.json"))
    if not files:
        problem(folder, "a color theme needs themes/*.json")
    for file in files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            problem(file, f"isn't valid JSON: {error}")
            continue
        variants = data.get("themes")
        if not isinstance(variants, list) or not variants:
            problem(file, "needs a themes list")
            continue
        names = set()
        for variant in variants:
            check_variant(file, variant, names)


def check_variant(file: Path, variant: dict, names: set) -> None:
    name = variant.get("name", "")
    where = f"{file.relative_to(ROOT).as_posix()} {name or '(no name)'}"
    if not name.startswith("LightLine "):
        problem(where, "variant names start with 'LightLine '")
    if name in names:
        problem(where, "named twice")
    names.add(name)
    appearance = variant.get("appearance")
    if appearance not in ("light", "dark"):
        problem(where, "appearance must be light or dark")
    style = variant.get("style", {})
    colors: dict[str, str] = {}
    for key in STYLE_KEYS:
        value = style.get(key)
        if not isinstance(value, str) or not COLOR.match(value):
            problem(where, f"{key} must be a #rrggbb or #rrggbbaa color")
        else:
            colors[key] = value
    players = style.get("players")
    if not (isinstance(players, list) and players and isinstance(players[0], dict)):
        problem(where, "needs players[0] with cursor and selection")
    else:
        for key in ("cursor", "selection"):
            value = players[0].get(key)
            if not isinstance(value, str) or not COLOR.match(value):
                problem(where, f"players[0].{key} must be a color")
    syntax = style.get("syntax", {})
    for key in SYNTAX_KEYS:
        value = syntax.get(key, {}).get("color") if isinstance(syntax.get(key), dict) else None
        if not isinstance(value, str) or not COLOR.match(value):
            problem(where, f"syntax.{key}.color must be a color")
        else:
            colors[f"syntax.{key}"] = value
    background = colors.get("editor.background")
    line = colors.get("editor.active_line.background")
    if not background or not line:
        return
    for key, value in colors.items():
        if not opaque(value) and (key in TEXT_KEYS or key.startswith("syntax.")):
            problem(where, f"{key} must be opaque, so its contrast is what you see")
    # AA (4.5:1) everywhere; AAA (7:1) for a high-contrast theme.
    least = 7.0 if name.endswith(" Contrast") else 4.5
    for key in TEXT_KEYS + [f"syntax.{k}" for k in SYNTAX_KEYS if k != "punctuation"]:
        if key not in colors:
            continue
        on_background = contrast(colors[key], background)
        on_line = contrast(colors[key], line)
        if on_background < least:
            problem(where, f"{key} is {on_background:.2f}:1 on the background, needs {least}")
        if on_line < 4.5:
            problem(where, f"{key} is {on_line:.2f}:1 on the caret line, needs 4.5")
    line_number = colors.get("editor.line_number")
    if line_number and contrast(line_number, background) < 3.0:
        problem(where, "editor.line_number needs 3:1 on the background")


def check_snippets(folder: Path, manifest: dict) -> None:
    files = manifest.get("snippets")
    files = [files] if isinstance(files, str) else files
    if not isinstance(files, list) or not files:
        problem(folder, "a snippet pack names its files in extension.toml: snippets = [...]")
        return
    for name in files:
        file = (folder / name).resolve()
        if folder.resolve() not in file.parents or file.suffix != ".json":
            problem(folder, f"{name} must be a .json file inside the extension")
            continue
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            problem(folder, f"{name} doesn't exist")
            continue
        except json.JSONDecodeError as error:
            problem(file, f"isn't valid JSON: {error}")
            continue
        if not isinstance(data, dict) or not data:
            problem(file, "needs at least one snippet")
            continue
        prefixes: set[str] = set()
        for title, snippet in data.items():
            check_snippet(file, title, snippet, prefixes)


def check_snippet(file: Path, title: str, snippet: dict, prefixes: set) -> None:
    where = f"{file.relative_to(ROOT).as_posix()} \"{title}\""
    if not isinstance(snippet, dict):
        problem(where, "must be an object with prefix and body")
        return
    prefix = snippet.get("prefix")
    for one in [prefix] if isinstance(prefix, str) else prefix or []:
        if not isinstance(one, str) or not one.strip():
            problem(where, "needs a prefix")
        elif one in prefixes:
            problem(where, f"prefix {one!r} is used twice in this file")
        else:
            prefixes.add(one)
    if not prefix:
        problem(where, "needs a prefix")
    body = snippet.get("body")
    if isinstance(body, list) and all(isinstance(line, str) for line in body):
        body = "\n".join(body)
    if not isinstance(body, str) or not body:
        problem(where, "needs a body: a string or a list of lines")
        return
    if not isinstance(snippet.get("description"), str):
        problem(where, "needs a description: it's shown in the completion list")
    check_body(where, body)


def check_body(where: str, body: str) -> None:
    # Escaped characters can't start or end anything.
    text = re.sub(r"\\[$}\\]", "", body)
    depth = 0
    for index, char in enumerate(text):
        if char == "$" and text[index + 1 : index + 2] == "{":
            depth += 1
        elif char == "}" and depth:
            depth -= 1
    if depth:
        problem(where, "a ${ is never closed")
    stops = re.findall(r"\$\{?(\d+)", text)
    repeated = sorted({stop for stop in stops if stops.count(stop) > 1 and stop != "0"})
    if repeated:
        # LightLine doesn't mirror a repeated tab stop: the second one comes
        # out empty. Repeat the text instead.
        problem(where, f"tab stop ${repeated[0]} is used more than once")
    if re.search(r"\$\{?[A-Za-z_]", text):
        # LightLine inserts nothing for $TM_FILENAME and other variables.
        problem(where, "uses a variable such as $TM_FILENAME, which LightLine leaves empty")


def main() -> int:
    seen: dict[str, Path] = {}
    count = 0
    for kind_folder, kind in KINDS.items():
        for folder in sorted((ROOT / kind_folder).glob("*/")):
            count += 1
            manifest = check_manifest(folder, template=False)
            if manifest is None:
                continue
            ident = manifest.get("id")
            if ident in seen:
                problem(folder, f"id {ident!r} is also used by {seen[ident].relative_to(ROOT)}")
            seen[ident] = folder
            if kind == "color-theme":
                check_theme(folder)
            else:
                check_snippets(folder, manifest)
    for kind_folder, kind in [("template/color-theme", "color-theme"), ("template/snippets", "snippets")]:
        folder = ROOT / kind_folder
        manifest = check_manifest(folder, template=True)
        if manifest is not None:
            check_theme(folder) if kind == "color-theme" else check_snippets(folder, manifest)
    for line in problems:
        print(line)
    if problems:
        print(f"\n{len(problems)} problem(s).")
        return 1
    print(f"{count} extensions and 2 templates checked: no problems.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
