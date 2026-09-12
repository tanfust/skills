#!/usr/bin/env python3
"""Structural validator for the tanfust/skills pack.

Standard library only. Exits non-zero when any check fails, naming the file
and the problem, so a malformed manifest or a renamed skill cannot reach main
and break installation silently.

Checks:
  - every skills/<dir> has a SKILL.md with YAML frontmatter
  - frontmatter `name` matches the directory exactly, lowercase kebab-case
  - `description` present, single line, under 1024 chars, and written as a
    trigger (names situations), not a topic label
  - no duplicate skill names anywhere in the repo
  - .claude-plugin/plugin.json and marketplace.json parse, agree on name,
    description and license, plugin `version` is semver, `source` resolves
  - every SKILL.md is under 500 lines (warning above 300)
  - the verification section is the final substantive section of SKILL.md
  - relative markdown links and same-file anchors resolve
  - LICENSE, README.md and the other repo furniture exist

Run:  python3 scripts/validate.py [repo-root]
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MAX_LINES = 500
WARN_LINES = 300
MAX_DESCRIPTION = 1024
MIN_DESCRIPTION = 60

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
TRIGGER_WORDS = re.compile(
    r"\b(use (this|it|when|whenever|for)|whenever|trigger|reach for|consult|"
    r"load (this|it)|apply (this|it)|invoke)\b",
    re.IGNORECASE,
)
VERIFY_HEADING = re.compile(r"\b(verif\w*|proof|prove|check\w*|test\w*|validat\w*)\b", re.IGNORECASE)
# A closing boundary statement may follow the verification section. Nothing else may.
TRAILING_ALLOWED = re.compile(r"^(where this (skill )?stops|scope|boundaries|out of scope)$", re.IGNORECASE)
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "out"}
REQUIRED_FILES = [
    "LICENSE",
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    ".gitignore",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
]

errors: list[str] = []
warnings: list[str] = []


def err(path, msg):
    errors.append(f"{path}: {msg}")


def warn(path, msg):
    warnings.append(f"{path}: {msg}")


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


# --------------------------------------------------------------------------- #
# Frontmatter
# --------------------------------------------------------------------------- #

def parse_frontmatter(text: str):
    """Top-level `key: value` frontmatter. Returns (dict, error).

    Uses PyYAML when it happens to be installed (it is what real installers
    use), and always runs the strict stdlib parser as well so CI without
    PyYAML still rejects the constructs a real parser would choke on."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, "missing YAML frontmatter (file must start with '---')"
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "frontmatter never closed (no second '---')"
    try:
        import yaml  # type: ignore
        try:
            parsed = yaml.safe_load("\n".join(lines[1:end]))
        except yaml.YAMLError as e:  # pragma: no cover
            return None, f"frontmatter is not valid YAML: {str(e).splitlines()[0]}"
        if not isinstance(parsed, dict):
            return None, "frontmatter is not a mapping"
    except ImportError:
        pass
    data = {}
    current = None
    for ln in lines[1:end]:
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if ln[0] in " \t":
            # continuation of a block or folded scalar, or nested structure
            if current is None:
                return None, f"unexpected indented frontmatter line: {ln!r}"
            data[current] = (data[current] + "\n" + ln.strip()).strip()
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", ln)
        if not m:
            return None, f"unparseable frontmatter line: {ln!r}"
        key, val = m.group(1), m.group(2).strip()
        if key in data:
            return None, f"duplicate frontmatter key '{key}'"
        if val in ("|", ">", "|-", ">-", "|+", ">+"):
            val = ""  # block scalar follows; continuation lines will be joined
        elif len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        elif val:
            # Unquoted plain scalar: the sequences below are YAML syntax, not text,
            # and a real parser rejects or misreads them. Quote the value instead.
            if ": " in val or val.endswith(":"):
                return None, f"'{key}' is an unquoted scalar containing ': ' (YAML reads it as a nested mapping). Quote the value or reword"
            if " #" in val:
                return None, f"'{key}' is an unquoted scalar containing ' #' (YAML starts a comment there). Quote the value"
            if val[0] in "[{&*!|>%@`":
                return None, f"'{key}' starts with '{val[0]}', which YAML treats as syntax. Quote the value"
        data[key] = val
        current = key
    return data, None


def github_slug(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[`*~]", "", s)  # GitHub keeps underscores in slugs
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s", "-", s)
    return s


def headings(text: str, level: int | None = None):
    out = []
    in_fence = False
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.startswith("```") or ln.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", ln)
        if m and (level is None or len(m.group(1)) == level):
            out.append((i, len(m.group(1)), m.group(2)))
    return out


# --------------------------------------------------------------------------- #
# Skill checks
# --------------------------------------------------------------------------- #

def check_skill(root: Path, skill_dir: Path, seen_names: dict):
    skill_md = skill_dir / "SKILL.md"
    r = rel(root, skill_md)
    if not skill_md.is_file():
        err(rel(root, skill_dir), "directory has no SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    fm, e = parse_frontmatter(text)
    if e:
        err(r, e)
        return

    name = fm.get("name", "")
    if not name:
        err(r, "frontmatter has no 'name'")
    else:
        if name != skill_dir.name:
            err(r, f"frontmatter name '{name}' does not match directory '{skill_dir.name}'")
        if not KEBAB.match(name):
            err(r, f"name '{name}' is not lowercase kebab-case")
        seen_names.setdefault(name, []).append(r)

    desc = fm.get("description", "")
    if not desc:
        err(r, "frontmatter has no 'description'")
    else:
        if "\n" in desc:
            err(r, "description spans multiple lines; it must be a single line")
        if len(desc) > MAX_DESCRIPTION:
            err(r, f"description is {len(desc)} chars; limit is {MAX_DESCRIPTION}")
        if len(desc) < MIN_DESCRIPTION:
            err(r, f"description is {len(desc)} chars; too short to state what it does and when to trigger")
        if not TRIGGER_WORDS.search(desc):
            err(r, "description reads like a topic label: it never says when to use the skill "
                   "(expected wording such as 'Use this whenever ...')")

    n_lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    if n_lines >= MAX_LINES:
        err(r, f"SKILL.md is {n_lines} lines; limit is {MAX_LINES}. Move detail into references/")
    elif n_lines > WARN_LINES:
        warn(r, f"SKILL.md is {n_lines} lines; consider moving detail into references/")

    # Verification must be the final substantive H2. A boundary section may trail it.
    h2 = headings(text, 2)
    if not h2:
        err(r, "no '## ' sections found; a verification section is required")
    else:
        idx = len(h2) - 1
        while idx > 0 and TRAILING_ALLOWED.match(h2[idx][2].strip()):
            idx -= 1
        final = h2[idx]
        title = re.sub(r"^\d+[.)]\s*", "", final[2])
        if not VERIFY_HEADING.search(title):
            err(r, f"final substantive section is '## {final[2]}' (line {final[0]}); "
                   "the last section must be the verification section")

    if "—" in text:
        warn(r, "contains an em dash; the framework style rule says not to use them")

    # references over 300 lines need a table of contents
    refs = skill_dir / "references"
    if refs.is_dir():
        for ref in sorted(refs.glob("*.md")):
            rt = ref.read_text(encoding="utf-8")
            if rt.count("\n") > 300:
                top = rt[:2000]
                if not re.search(r"^\s*[-*]\s+\[.+\]\(#.+\)", top, re.M):
                    warn(rel(root, ref), "over 300 lines and no table of contents at the top")


# --------------------------------------------------------------------------- #
# Manifests
# --------------------------------------------------------------------------- #

def load_json(root: Path, p: Path):
    r = rel(root, p)
    if not p.is_file():
        err(r, "missing")
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(r, f"invalid JSON: {e.msg} at line {e.lineno} column {e.colno}")
        return None


def check_manifests(root: Path, skill_names: set):
    plugin_p = root / ".claude-plugin" / "plugin.json"
    market_p = root / ".claude-plugin" / "marketplace.json"
    plugin = load_json(root, plugin_p)
    market = load_json(root, market_p)
    if plugin is None or market is None:
        return
    pr, mr = rel(root, plugin_p), rel(root, market_p)

    for key in ("name", "version", "description", "license"):
        if not plugin.get(key):
            err(pr, f"missing '{key}'")
    if plugin.get("name") and not KEBAB.match(plugin["name"]):
        err(pr, f"plugin name '{plugin['name']}' is not lowercase kebab-case")
    if plugin.get("version") and not SEMVER.match(str(plugin["version"])):
        err(pr, f"version '{plugin['version']}' is not semver")

    for key in ("name", "owner", "plugins"):
        if key not in market:
            err(mr, f"missing '{key}'")
    plugins = market.get("plugins") or []
    if not isinstance(plugins, list) or not plugins:
        err(mr, "'plugins' must be a non-empty list")
        return

    match = [p for p in plugins if isinstance(p, dict) and p.get("name") == plugin.get("name")]
    if not match:
        err(mr, f"no plugins[] entry named '{plugin.get('name')}' (plugin.json name)")
        return
    entry = match[0]
    for key in ("description", "license"):
        if entry.get(key) != plugin.get(key):
            err(mr, f"plugins[].{key} disagrees with plugin.json {key}:\n"
                    f"      marketplace: {entry.get(key)!r}\n"
                    f"      plugin.json: {plugin.get(key)!r}")
    src = entry.get("source")
    if not src:
        err(mr, "plugins[].source is missing")
    elif isinstance(src, str):
        target = (root / src).resolve()
        if not target.is_dir():
            err(mr, f"plugins[].source '{src}' does not resolve to a directory")
        elif not (target / ".claude-plugin" / "plugin.json").is_file():
            err(mr, f"plugins[].source '{src}' has no .claude-plugin/plugin.json")
        elif not (target / "skills").is_dir():
            err(mr, f"plugins[].source '{src}' has no skills/ directory")

    # If plugin.json enumerates skills explicitly, each must exist.
    listed = plugin.get("skills")
    if isinstance(listed, list):
        for s in listed:
            p = (root / str(s)).resolve()
            if not (p / "SKILL.md").is_file() and not p.is_file():
                err(pr, f"skills[] entry '{s}' does not resolve to a skill")


# --------------------------------------------------------------------------- #
# Links
# --------------------------------------------------------------------------- #

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def check_links(root: Path, md_files):
    for md in md_files:
        r = rel(root, md)
        text = md.read_text(encoding="utf-8")
        slugs = {github_slug(h[2]) for h in headings(text)}
        in_fence = False
        for i, ln in enumerate(text.splitlines(), 1):
            if ln.startswith("```") or ln.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in LINK.finditer(ln):
                target = m.group(1)
                if re.match(r"^[a-z][a-z0-9+.-]*:", target):  # http:, mailto:, etc.
                    continue
                if target.startswith("#"):
                    if target[1:] not in slugs:
                        err(r, f"line {i}: anchor '{target}' matches no heading in this file")
                    continue
                path_part, _, frag = target.partition("#")
                dest = (md.parent / path_part).resolve()
                if not dest.exists():
                    err(r, f"line {i}: link target '{target}' does not exist")
                    continue
                if frag and dest.is_file() and dest.suffix == ".md":
                    dtext = dest.read_text(encoding="utf-8")
                    if frag not in {github_slug(h[2]) for h in headings(dtext)}:
                        err(r, f"line {i}: anchor '#{frag}' not found in {rel(root, dest)}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def walk_md(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(".md"):
                yield Path(dirpath) / f


def main(argv):
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path(__file__).resolve().parent.parent
    print(f"validating {root}")

    for f in REQUIRED_FILES:
        p = root / f
        if not p.is_file():
            err(f, "missing")
        elif p.stat().st_size == 0:
            err(f, "is empty")

    lic = root / "LICENSE"
    if lic.is_file() and lic.stat().st_size > 0:
        lt = lic.read_text(encoding="utf-8")
        if "MIT License" not in lt:
            err("LICENSE", "does not look like the MIT license")
        if not re.search(r"^Copyright \(c\) \d{4} .+", lt, re.M):
            err("LICENSE", "has no 'Copyright (c) <year> <holder>' line")

    skills_root = root / "skills"
    if not skills_root.is_dir():
        err("skills", "directory missing")
    skill_dirs = sorted(p for p in skills_root.iterdir() if p.is_dir()) if skills_root.is_dir() else []
    if not skill_dirs:
        err("skills", "contains no skill directories")

    seen: dict = {}
    for d in skill_dirs:
        check_skill(root, d, seen)

    # duplicate names anywhere in the repo, not just under skills/
    all_md = list(walk_md(root))
    for md in all_md:
        if md.name == "SKILL.md" and md.parent.parent != skills_root:
            fm, e = parse_frontmatter(md.read_text(encoding="utf-8"))
            if fm and fm.get("name"):
                seen.setdefault(fm["name"], []).append(rel(root, md))
    for name, files in seen.items():
        if len(files) > 1:
            err(", ".join(files), f"duplicate skill name '{name}'")

    check_manifests(root, set(seen))
    check_links(root, all_md)

    print(f"checked {len(skill_dirs)} skill(s), {len(all_md)} markdown file(s)")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\nFAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"\nOK: 0 errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
