#!/usr/bin/env python3
"""The pieces of the zae plugin that were picked from other people's plugins.

A component is one skill folder, or one agent, command or output-style file,
copied into plugins/zae/ from an upstream git repository at a pinned commit.
plugins/zae/vendored.json records where each came from and a hash of what was copied.
Anything under plugins/zae/ that vendored.json does not list is our own and
this script leaves it alone.

  add <upstream> [<path>] [--as <dest>] [--ref <commit>]
                   pick a component. <upstream> is owner/repo, a git URL, or a
                   GitHub tree/blob URL (which also gives the ref and path)
  update <dest> [--ref <commit>]
                   re-copy a component at <commit> (default: upstream HEAD)
  update --all     the same for every component
  remove <dest>    drop a component and its record
  status           each component's pin against upstream HEAD (network;
                   exit 2 = an update is available)
  check            the copied files equal what vendored.json records
  install          add the zeroae.com marketplace from GitHub (zeroae/.claude)
                   and install zae@zeroae.com (once per machine)

<dest> is the component's path inside plugins/zae, e.g. skills/unslop.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "zae"
LICENSES = PLUGIN / "licenses"
LOCK = PLUGIN / "vendored.json"
CATALOGUE = ROOT / ".claude-plugin" / "marketplace.json"
GITHUB_REPO = "zeroae/.claude"
# Where each kind lives in a plugin, and whether it is a folder or one .md file.
KINDS = {"skills": "dir", "agents": "file", "commands": "file", "output-styles": "file"}
# Upstream files a component does not need, at any depth.
SKIP = {".git", "node_modules", ".github", ".DS_Store"}
# Frontmatter keys that change what Claude may run or reach: review them on every update.
REVIEW_KEYS = ("hooks", "allowed-tools", "tools", "mcpServers", "permissionMode", "model")
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING")


def die(msg: str) -> None:
    print(f"zae: {msg}", file=sys.stderr)
    sys.exit(1)


def load_lock() -> dict:
    return json.loads(LOCK.read_text())


def save_lock(lock: dict) -> None:
    lock["components"] = dict(sorted(lock["components"].items()))
    LOCK.write_text(json.dumps(lock, indent=2) + "\n")


def git(*args: str, cwd: Path | None = None) -> str:
    run = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if run.returncode != 0:
        die(f"git {' '.join(args)} failed:\n{run.stderr.strip()}")
    return run.stdout.strip()


def fetch(url: str, ref: str, dest: Path, *, blobs: bool = True) -> str:
    git("init", "-q", str(dest))
    git("fetch", "-q", "--depth", "1", *([] if blobs else ["--filter=blob:none"]), url, ref, cwd=dest)
    return git("rev-parse", "FETCH_HEAD", cwd=dest)


def object_of(clone: Path, path: str) -> str:
    """The git object id of the component: equal ids mean identical content."""
    return git("rev-parse", f"FETCH_HEAD:{path}", cwd=clone)


def files_of(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(p for p in target.rglob("*") if p.is_file() and not p.is_symlink())


def symlinks(target: Path) -> list[str]:
    if target.is_symlink():
        return [target.name]
    if not target.is_dir():
        return []
    return sorted(p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_symlink())


def content_hash(target: Path) -> str:
    """sha256 over every file's relative path, exec bit and bytes, in sorted order."""
    h = hashlib.sha256()
    base = target.parent if target.is_file() else target
    for path in files_of(target):
        rel = path.relative_to(base).as_posix()
        mode = b"x" if path.stat().st_mode & 0o111 else b"-"
        h.update(rel.encode() + b"\0" + mode)
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def frontmatter(md: Path) -> tuple[str, list[str]]:
    """(name, the lines that set a REVIEW_KEYS key) from a markdown file's frontmatter."""
    text = md.read_text(errors="replace")
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return "", []
    name, review = "", []
    for line in m.group(1).splitlines():
        key = line.split(":", 1)[0].strip()
        if key == "name" and not line.startswith(" "):
            name = line.split(":", 1)[1].strip().strip("\"'")
        if key in REVIEW_KEYS and not line.startswith(" "):
            review.append(line.strip())
    return name, review


def needs_review(target: Path) -> list[str]:
    """What in a component can run something or widen Claude's permissions."""
    md = target / "SKILL.md" if target.is_dir() else target
    found = [f"frontmatter {line}" for line in frontmatter(md)[1]] if md.is_file() else []
    base = target.parent if target.is_file() else target
    found += [
        f"executable {p.relative_to(base).as_posix()}"
        for p in files_of(target)
        if p.stat().st_mode & 0o111
    ]
    return found


def parse_upstream(upstream: str, path: str | None, ref: str | None) -> tuple[str, str, str | None]:
    """(git url, path in repo, ref or None) from owner/repo, a git URL, or a GitHub tree/blob URL."""
    m = re.match(r"https://github\.com/([^/]+/[^/]+)/(?:tree|blob)/([^/]+)/(.+?)/?$", upstream)
    if m:
        repo, url_ref, url_path = m.groups()
        return f"https://github.com/{repo}.git", path or url_path, ref or url_ref
    if re.fullmatch(r"[\w.-]+/[\w.-]+", upstream):
        upstream = f"https://github.com/{upstream}.git"
    if not path:
        die("give the component's path in the upstream repo, or a GitHub tree/blob URL")
    return upstream, path.strip("/"), ref


def infer_dest(source: Path, path: str) -> str:
    parts = path.split("/")
    if source.is_dir():
        if not (source / "SKILL.md").is_file():
            die(f"{path} is a folder without SKILL.md; only skills are folders. Pass --as to say what it is")
        return f"skills/{parts[-1]}"
    for kind, shape in KINDS.items():
        if shape == "file" and kind in parts[:-1] and path.endswith(".md"):
            return f"{kind}/{parts[-1]}"
    die(f"cannot tell what kind of component {path} is; pass --as <kind>/<name>")
    return ""


def check_dest(dest: str) -> None:
    kind, _, name = dest.partition("/")
    if kind not in KINDS or not name or "/" in name:
        die(f"{dest}: expected one of {', '.join(f'{k}/<name>' for k in KINDS)}")
    if KINDS[kind] == "file" and not name.endswith(".md"):
        die(f"{dest}: {kind} are single .md files")


def find_license(clone: Path, path: str) -> Path | None:
    """The license nearest the component, walking up to the repo root."""
    here = clone / path
    for folder in [here, *here.parents]:
        for name in LICENSE_NAMES:
            if (folder / name).is_file():
                return folder / name
        if folder == clone:
            break
    return None


def spdx_guess(text: str) -> str:
    head = text[:400]
    for marker, spdx in (
        ("MIT License", "MIT"),
        ("Permission is hereby granted, free of charge", "MIT"),
        ("Apache License", "Apache-2.0"),
        ("BSD 3-Clause", "BSD-3-Clause"),
        ("BSD 2-Clause", "BSD-2-Clause"),
        ("Mozilla Public License", "MPL-2.0"),
        ("GNU GENERAL PUBLIC LICENSE", "GPL"),
        ("ISC License", "ISC"),
        ("CC0", "CC0-1.0"),
    ):
        if marker in head:
            return spdx
    return "unknown"


def license_slug(url: str, license_dir: str) -> str:
    repo = re.sub(r"^https?://[^/]+/|\.git$", "", url).replace("/", "__")
    return f"{repo}__{license_dir.replace('/', '-')}.txt" if license_dir else f"{repo}.txt"


def vendor(dest: str, rec: dict, ref: str | None, *, allow_unlicensed: bool = False) -> bool:
    """Copy the component at ref (default HEAD) into plugins/zae/<dest>. True if it changed."""
    target = PLUGIN / dest
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "src"
        commit = fetch(rec["upstream"], ref or "HEAD", clone)
        obj = object_of(clone, rec["path"])
        intact = target.exists() and content_hash(target) == rec.get("content_sha256")
        if rec.get("ref") and obj == rec.get("object") and intact:
            print(f"{dest}: unchanged (same content at {commit[:12]}); nothing to do")
            return False
        git("checkout", "-q", "FETCH_HEAD", cwd=clone)
        source = clone / rec["path"]
        if symlinks(source):
            die(f"{dest}: upstream has symlinks, which are refused: {symlinks(source)}")
        found = find_license(clone, rec["path"])
        if found is None and not allow_unlicensed:
            die(f"{rec['upstream']} has no LICENSE near {rec['path']}; without one you may not copy it. "
                "Pass --allow-unlicensed only if you have permission")
        before = needs_review(target) if target.exists() else []
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=lambda _, names: {n for n in names if n in SKIP})
        else:
            shutil.copy2(source, target)
        license_file = ""
        if found is not None:
            license_file = license_slug(rec["upstream"], found.parent.relative_to(clone).as_posix().strip("."))
            LICENSES.mkdir(parents=True, exist_ok=True)
            shutil.copy2(found, LICENSES / license_file)
            spdx = spdx_guess(found.read_text(errors="replace"))
        else:
            spdx = "none"
    after = needs_review(target)
    old = rec.get("ref", "")
    rec.update(
        ref=commit,
        object=obj,
        license=spdx,
        license_file=f"licenses/{license_file}" if license_file else "",
        vendored_on=datetime.date.today().isoformat(),
        content_sha256=content_hash(target),
        needs_review=after,
    )
    print(f"{dest}: {old[:12] or 'new'} -> {commit[:12]} (license {spdx})")
    md = target / "SKILL.md" if target.is_dir() else target
    name = frontmatter(md)[0] if md.is_file() else ""
    stem = Path(dest).name.removesuffix(".md")
    if name and name != stem:
        print(f"NOTE: its frontmatter says name: {name}, but it lives at {dest}. Rename one so they agree")
    if after != before:
        print("REVIEW: what this component can run or widen changed:")
        for line in sorted(set(before) - set(after)):
            print(f"  - {line}")
        for line in sorted(set(after) - set(before)):
            print(f"  + {line}")
    if old and old != commit and rec["upstream"].startswith("https://github.com/"):
        print(f"Upstream changes: {rec['upstream'].removesuffix('.git')}/compare/{old}...{commit}")
    return True


def add(upstream: str, path: str | None, dest: str | None, ref: str | None, allow_unlicensed: bool) -> int:
    url, path, ref = parse_upstream(upstream, path, ref)
    if dest is None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "src"
            fetch(url, ref or "HEAD", clone)
            git("checkout", "-q", "FETCH_HEAD", cwd=clone)
            if not (clone / path).exists():
                die(f"{url} has no {path}")
            dest = infer_dest(clone / path, path)
    check_dest(dest)
    lock = load_lock()
    if dest in lock["components"]:
        die(f"{dest} is already vendored; use `update {dest}`")
    if (PLUGIN / dest).exists():
        die(f"plugins/zae/{dest} exists and is our own; pick another name with --as")
    rec = {"upstream": url, "path": path}
    vendor(dest, rec, ref, allow_unlicensed=allow_unlicensed)
    lock["components"][dest] = rec
    save_lock(lock)
    print(f"Call it as /zae:{Path(dest).name.removesuffix('.md')} in a new session (or after /reload-plugins).")
    return 0


def update(dest: str | None, ref: str | None, every: bool) -> int:
    lock = load_lock()
    targets = list(lock["components"]) if every else [dest]
    if every and ref:
        die("--ref applies to one component, not --all")
    for d in targets:
        if d not in lock["components"]:
            die(f"{d} is not vendored; `add` it first")
        vendor(d, lock["components"][d], ref, allow_unlicensed=lock["components"][d].get("license") == "none")
        save_lock(lock)
    return 0


def remove(dest: str) -> int:
    lock = load_lock()
    rec = lock["components"].pop(dest, None)
    if rec is None:
        die(f"{dest} is not vendored")
    target = PLUGIN / dest
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    still_used = {r.get("license_file") for r in lock["components"].values()}
    if rec.get("license_file") and rec["license_file"] not in still_used:
        (PLUGIN / rec["license_file"]).unlink(missing_ok=True)
    save_lock(lock)
    print(f"{dest}: removed")
    return 0


def check() -> int:
    lock = load_lock()["components"]
    problems = []
    for dest, rec in lock.items():
        target = PLUGIN / dest
        if not target.exists():
            problems.append(f"{dest}: plugins/zae/{dest} is missing")
        elif symlinks(target):
            problems.append(f"{dest}: symlinks are refused: {symlinks(target)}")
        elif content_hash(target) != rec["content_sha256"]:
            problems.append(
                f"{dest}: its files differ from what vendored.json records. Either restore it with "
                f"`scripts/zae-vendor.py update {dest} --ref {rec['ref']}`, or make it our own with "
                f"`scripts/zae-vendor.py remove {dest}` and write it back by hand"
            )
        if rec.get("license_file") and not (PLUGIN / rec["license_file"]).is_file():
            problems.append(f"{dest}: plugins/zae/{rec['license_file']} is missing")
    for kind in KINDS:
        for entry in sorted((PLUGIN / kind).glob("*")) if (PLUGIN / kind).is_dir() else []:
            if entry.is_symlink():
                problems.append(f"{kind}/{entry.name}: symlinks are refused")
    for p in problems:
        print(f"FAIL {p}")
    own = [
        f"{k}/{e.name}"
        for k in KINDS
        if (PLUGIN / k).is_dir()
        for e in sorted((PLUGIN / k).iterdir())
        if f"{k}/{e.name}" not in lock and e.name != ".gitkeep"
    ]
    if not problems:
        print(f"ok: {len(lock)} vendored components match vendored.json; {len(own)} of our own")
    return 1 if problems else 0


def status() -> int:
    """Exit 2 when an update is available, so a scheduled job can act on it."""
    behind = False
    heads: dict[str, tuple[str, Path]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for dest, rec in load_lock()["components"].items():
            url = rec["upstream"]
            if url not in heads:
                clone = Path(tmp) / str(len(heads))
                heads[url] = (fetch(url, "HEAD", clone, blobs=False), clone)
            head, clone = heads[url]
            try:
                obj = object_of(clone, rec["path"])
            except SystemExit:
                behind = True
                print(f"{dest}: {rec['path']} is gone from {url} HEAD: decide whether to keep it")
                continue
            current = head == rec["ref"] or obj == rec["object"]
            behind = behind or not current
            state = "up to date" if current else f"update available: {head[:12]}"
            print(f"{dest}: pinned {rec['ref'][:12]} ({rec['vendored_on']}), {state}")
    return 2 if behind else 0


def install() -> int:
    if shutil.which("claude") is None:
        die("the `claude` CLI is not on PATH")
    market = json.loads(CATALOGUE.read_text())["name"]
    added = subprocess.run(["claude", "plugin", "marketplace", "add", GITHUB_REPO])
    if added.returncode != 0:
        subprocess.run(["claude", "plugin", "marketplace", "update", market], check=True)
    subprocess.run(["claude", "plugin", "install", f"zae@{market}"], check=True)
    print("Done. Start a new Claude Code session (or run /reload-plugins) to load it.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("upstream")
    a.add_argument("path", nargs="?")
    a.add_argument("--as", dest="dest")
    a.add_argument("--ref")
    a.add_argument("--allow-unlicensed", action="store_true")
    u = sub.add_parser("update")
    u.add_argument("dest", nargs="?")
    u.add_argument("--ref")
    u.add_argument("--all", action="store_true")
    r = sub.add_parser("remove")
    r.add_argument("dest")
    sub.add_parser("status")
    sub.add_parser("check")
    sub.add_parser("install")
    args = ap.parse_args()
    if args.cmd == "add":
        return add(args.upstream, args.path, args.dest, args.ref, args.allow_unlicensed)
    if args.cmd == "update":
        if not args.all and not args.dest:
            ap.error("update needs <dest> or --all")
        return update(args.dest, args.ref, args.all)
    if args.cmd == "remove":
        return remove(args.dest)
    if args.cmd == "status":
        return status()
    if args.cmd == "check":
        return check()
    return install()


if __name__ == "__main__":
    sys.exit(main())
