#!/usr/bin/env python3
"""GHOBS check and sync. Standard library only, one file, easy to read.

  python ghobs.py check [--path DIR] [--site-root DIR] [--warn-only] [--strict]
  python ghobs.py sync --standard-dir DIR [--path DIR] [--init]

Rules live in the standard repo under rules/. Exceptions go in app.yml.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

BEGIN_RE = re.compile(r"<!-- GHOBS:BEGIN v([\w.\-]+) -->")
END = "<!-- GHOBS:END -->"
SKIP_DIRS = {".git", "node_modules", ".ghobs", ".ghobs-src", "vendor", "dist", "build", "__pycache__", ".venv", "venv"}
CODE_EXT = {".html", ".htm", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".css", ".py", ".jinja", ".j2", ".vue", ".svelte", ".astro"}
MAX_BYTES = 1_000_000

# ---------------------------------------------------------------- small yaml

def strip_comment(line):
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out)


def unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_yaml(text):
    """Tiny YAML subset: nested 'key: value' maps, indentation based, no lists."""
    root = {}
    stack = [(-1, root)]
    for raw in text.splitlines():
        line = strip_comment(raw).rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip())
        key, _, value = line.strip().partition(":")
        value = value.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child = {}
            parent[key.strip()] = child
            stack.append((indent, child))
        else:
            parent[key.strip()] = unquote(value)
    return root

# ---------------------------------------------------------------- file helpers

def tracked_files(root):
    files = []
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=True).stdout
        files = [root / p for p in out.split("\n") if p]
    except Exception:
        pass
    if not files:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            files += [Path(dirpath) / f for f in filenames]
    return [f for f in files if f.is_file() and not (set(f.relative_to(root).parts) & SKIP_DIRS)]


def read_text(path):
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def extract_block(text):
    m = BEGIN_RE.search(text or "")
    if not m:
        return None
    end = text.find(END, m.end())
    if end == -1:
        return None
    return text[m.start():end + len(END)].replace("\r\n", "\n")

# ---------------------------------------------------------------- checks

ENUMS = {
    "platform": {"docker", "worker", "pages", "other"},
    "ui": {"desktop-admin", "responsive", "none"},
    "audience": {"internal", "clients", "resale", "public"},
    "api": {"true", "false"},
    "mcp": {"true", "false"},
}
WORDS = {"unanswered", "skipped"}
FA_CDN = re.compile(r"(kit|use)\.fontawesome\.com|cdnjs\.cloudflare\.com/ajax/libs/font-awesome|cdn\.jsdelivr\.net/npm/@fortawesome|unpkg\.com/@fortawesome|bootstrapcdn\.com/font-awesome")
NEG_TOGGLE = re.compile(r"""(?:\b(?:disable|disabled|hide)_[a-z0-9_]+["']?\s*[:=]|name=["'](?:disable|disabled|hide)_)""")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})")
OK_DOMAINS = ("example.com", "example.org", "example.net", "localhost", "noreply.github.com", "users.noreply.github.com")
OK_SUFFIX = (".test", ".invalid", ".example", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js", ".ico")
SECRET = re.compile(r"(sk_live_[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|xox[bp]-[0-9A-Za-z-]{20,})")
SECRET_NAMES = (".sqlite", ".sqlite3", ".db", ".pem", ".pfx", ".p12", ".key")
SAFE_NAMES = {"Thumbs.db", ".DS_Store"}


def f(rule, level, path, line, msg):
    return (rule, level, str(path), line, msg)


def version_tuple(text):
    return tuple(int(n) for n in re.findall(r"\d+", text or "")[:3])


def check_app_yml(root, app):
    out = []
    if app is None:
        return [f("APP-001", "ERROR", "app.yml", 0, "missing app.yml (run: python .ghobs/ghobs.py sync --init)")]
    for key in ("standard", "name", "platform", "ui"):
        if not app.get(key):
            out.append(f("APP-001", "ERROR", "app.yml", 0, f"missing key: {key}"))
    if not isinstance(app.get("docs"), dict) or not app["docs"].get("mode"):
        out.append(f("APP-001", "ERROR", "app.yml", 0, "missing key: docs.mode"))
    for key, allowed in ENUMS.items():
        value = app.get(key)
        if value and value not in allowed | WORDS:
            out.append(f("APP-001", "ERROR", "app.yml", 0, f"{key} must be one of {sorted(allowed)}, got '{value}'"))
    if "website" in app and app["website"] != "public":
        out.append(f("APP-001", "ERROR", "app.yml", 0, "website must be public or omitted"))
    docs = app.get("docs") if isinstance(app.get("docs"), dict) else {}
    if docs.get("mode") and docs["mode"] not in {"in-repo", "docusaurus-repo"} | WORDS:
        out.append(f("APP-001", "ERROR", "app.yml", 0, "docs.mode must be in-repo or docusaurus-repo"))
    for key in ("name", "platform", "ui", "audience", "api", "mcp", "brand_kit", "organization"):
        if app.get(key) == "unanswered":
            out.append(f("DOC-002", "WARN", "app.yml", 0, f"onboarding question not answered yet: {key} (answer it or set it to skipped)"))
    if docs.get("mode") == "unanswered":
        out.append(f("DOC-002", "WARN", "app.yml", 0, "onboarding question not answered yet: docs.mode"))
    if docs.get("mode") == "docusaurus-repo" and not docs.get("repo"):
        out.append(f("DOC-001", "ERROR", "app.yml", 0, "docs.mode is docusaurus-repo but docs.repo is empty"))
    if docs.get("mode") == "in-repo" and not (root / "docs").is_dir() and not (root / "README.md").exists():
        out.append(f("DOC-001", "WARN", "README.md", 0, "docs.mode is in-repo but there is no docs/ folder or README.md"))
    return out


def check_ai_files(root):
    out = []
    agents = root / "AGENTS.md"
    block = extract_block(read_text(agents)) if agents.exists() else None
    if not block:
        return [f("AI-001", "ERROR", "AGENTS.md", 0, "missing or no GHOBS managed block (run sync)")]
    for name in ("CLAUDE.md", "GEMINI.md"):
        text = read_text(root / name) if (root / name).exists() else None
        if text is None or "@AGENTS.md" not in text:
            out.append(f("AI-001", "ERROR", name, 0, "missing or does not import @AGENTS.md"))
    for name in (".github/copilot-instructions.md", ".cursor/rules/ghobs.mdc"):
        text = read_text(root / name) if (root / name).exists() else None
        if extract_block(text) != block:
            out.append(f("AI-001", "ERROR", name, 0, "missing or differs from the AGENTS.md block (run sync)"))
    return out


def scan_lines(files, root, exts, pattern, rule, level, msg, limit=5):
    out = []
    for path in files:
        if path.suffix.lower() not in exts:
            continue
        text = read_text(path)
        if not text:
            continue
        hits = 0
        for n, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                out.append(f(rule, level, path.relative_to(root), n, msg))
                hits += 1
                if hits >= limit:
                    break
    return out


def is_test_file(rel):
    parts = {p.lower() for p in rel.parts}
    name = rel.name.lower()
    return bool(parts & {"tests", "test", "__tests__", "fixtures"}) or name.startswith("test_") or ".test." in name or ".spec." in name


def check_placeholders(files, root, own_domains=()):
    out = []
    for path in files:
        if path.suffix.lower() not in CODE_EXT | {".md", ".json", ".yml", ".yaml"} or path.name in {"package-lock.json", "app.yml"}:
            continue
        if is_test_file(path.relative_to(root)):
            continue
        text = read_text(path)
        if not text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in EMAIL.finditer(line):
                domain = m.group(1).lower()
                if domain in OK_DOMAINS or domain in own_domains or domain.endswith(OK_SUFFIX):
                    continue
                out.append(f("PH-001", "WARN", path.relative_to(root), n, f"email at a real-looking domain ({domain}); use example.com or a fictional name"))
                break
    deny_path = Path(os.environ["GHOBS_DENYLIST"]) if os.environ.get("GHOBS_DENYLIST") else root / ".ghobs-denylist"
    terms = []
    if deny_path.exists():
        terms = [t.strip().lower() for t in deny_path.read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]
    for path in files:
        if not terms or path.name == ".ghobs-denylist":
            continue
        text = read_text(path)
        if not text:
            continue
        low = text.lower()
        for term in terms:
            if term in low:
                n = next((i for i, line in enumerate(low.splitlines(), 1) if term in line), 0)
                out.append(f("PH-001", "ERROR", path.relative_to(root), n, "contains a term from the private denylist (real client, person or company)"))
    return out


def check_secrets(files, root):
    out = []
    for path in files:
        rel = path.relative_to(root)
        name = path.name
        if name in SAFE_NAMES:
            continue
        env_like = name == ".env" or (name.startswith(".env.") and not name.endswith((".example", ".sample", ".template"))) or name == ".dev.vars"
        if env_like or name.lower().endswith(SECRET_NAMES):
            out.append(f("SEC-001", "ERROR", rel, 0, "secret or data file is tracked in git (remove it and add to .gitignore)"))
            continue
        text = read_text(path)
        if text:
            for n, line in enumerate(text.splitlines(), 1):
                if SECRET.search(line):
                    out.append(f("SEC-001", "ERROR", rel, n, "looks like a real credential; rotate it and remove it from git"))
                    break
    if not (root / ".gitignore").exists():
        out.append(f("SEC-001", "WARN", ".gitignore", 0, "missing .gitignore"))
    return out


def version_findings(path, label, declared, item):
    """Error below the minimum, warn when a newer minor line exists than the declared one."""
    have = version_tuple(declared)
    out = []
    minimum, target = item.get("minimum", ""), item.get("target", "")
    if have and minimum and have < version_tuple(minimum):
        out.append(f("API-002", "ERROR", path, 0, f"{label} {declared} is below the minimum {minimum} (latest stable is {target or minimum})"))
    elif have and target and have[:2] < version_tuple(target)[:2]:
        out.append(f("API-002", "WARN", path, 0, f"{label} {declared} is behind the latest stable {target}"))
    return out


def check_api(files, root, app, standard_versions):
    out = []
    if app and app.get("api") == "true":
        blob = ""
        for path in files:
            if path.suffix.lower() in {".py", ".js", ".mjs", ".ts"}:
                blob += read_text(path) or ""
        for needle in ("/healthz", "/api/openapi.json", "/api/docs"):
            if blob.strip() and needle not in blob:  # no source yet (planning phase): nothing to check
                out.append(f("API-002", "ERROR", "(source)", 0, f"api is true but {needle} was not found in the source"))
    items = standard_versions.get("items", {}) if standard_versions else {}
    spec = root / "openapi" / "openapi.json"
    if spec.exists():
        try:
            declared = json.loads(spec.read_text(encoding="utf-8")).get("openapi", "")
        except ValueError:
            declared = ""
        out += version_findings("openapi/openapi.json", "OpenAPI", declared, items.get("openapi", {}))
    package = root / "package.json"
    if package.exists():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
        wanted = {**data.get("devDependencies", {}), **data.get("dependencies", {})}.get("swagger-ui-dist")
        if wanted:
            out += version_findings("package.json", "Swagger UI (swagger-ui-dist)", wanted, items.get("swagger-ui", {}))
    if app and app.get("mcp") == "true":
        manifests = [root / n for n in ("requirements.txt", "pyproject.toml") if (root / n).exists()]
        if manifests and not any("fastmcp" in (read_text(m) or "").lower() for m in manifests):
            out.append(f("MCP-001", "WARN", "requirements.txt", 0, "mcp is true but FastMCP is not a dependency"))
    return out


SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def check_public_site_output(site_root):
    """Check explicit local discovery artifacts, not hosting or accessibility."""
    out = []
    robots = read_text(site_root / "robots.txt") or ""
    if not re.search(r"^[ \t]*User-agent:[ \t]*[^\s#]", robots.lstrip("\ufeff"), re.I | re.M):
        out.append(f("WEB-002", "ERROR", "robots.txt", 0, "expected a public robots.txt with a User-agent directive"))

    try:
        sitemap = site_root / "sitemap.xml"
        # The standard uncompressed limit is 50 MB.
        if sitemap.stat().st_size > 52_428_800:
            raise ValueError("sitemap exceeds 50 MB")
        root = ElementTree.parse(sitemap).getroot()
        kinds = {SITEMAP_NS + "urlset": "url", SITEMAP_NS + "sitemapindex": "sitemap"}
        entry = kinds.get(root.tag)
        if not entry:
            raise ValueError("expected a sitemap urlset or sitemapindex")
        entries = root.findall(SITEMAP_NS + entry)
        if not entries:
            raise ValueError("sitemap has no entries")
        for item in entries:
            loc = (item.findtext(SITEMAP_NS + "loc") or "").strip()
            url = urlsplit(loc)
            if url.scheme not in {"https", "http"} or not url.hostname or any(c.isspace() for c in loc):
                raise ValueError("each sitemap entry needs an absolute HTTP(S) loc")
    except (OSError, ElementTree.ParseError, ValueError) as err:
        reason = str(err) if isinstance(err, ValueError) else "missing or invalid XML"
        out.append(f("WEB-002", "ERROR", "sitemap.xml", 0, reason))

    llms = read_text(site_root / "llms.txt") or ""
    heading = next((line for line in llms.lstrip("\ufeff").splitlines() if line.strip()), "")
    if not re.match(r"^#[ \t]+\S", heading):
        out.append(f("WEB-003", "ERROR", "llms.txt", 0, "expected a public llms.txt starting with a Markdown H1"))
    return out


def run_check(root, warn_only=False, strict=False, site_root=None):
    root = Path(root).resolve()
    app_path = root / "app.yml"
    app = parse_yaml(app_path.read_text(encoding="utf-8")) if app_path.exists() else None
    versions_path = root / ".ghobs" / "versions.yml"
    versions = parse_yaml(versions_path.read_text(encoding="utf-8")) if versions_path.exists() else {}
    files = tracked_files(root)
    code = [p for p in files if p.suffix.lower() in CODE_EXT]

    findings = check_app_yml(root, app) + check_ai_files(root)
    if app and app.get("website") == "public" and site_root is not None:
        findings += check_public_site_output(root / site_root)
    findings += scan_lines(code, root, CODE_EXT, FA_CDN, "UI-002", "ERROR", "Font Awesome loaded from a CDN; self-host only the icons used")
    findings += scan_lines(files, root, CODE_EXT | {".json", ".yml", ".yaml", ".py"}, NEG_TOGGLE, "UI-001", "WARN", "setting named as a negative (disable_/hide_); name it positively, on means enabled")
    own = tuple(d.strip().lower() for d in (app or {}).get("own_domains", "").split(",") if d.strip())
    findings += check_placeholders(files, root, own) + check_secrets(files, root) + check_api(files, root, app, versions)

    exceptions = app.get("exceptions", {}) if app and isinstance(app.get("exceptions"), dict) else {}
    findings = [x for x in findings if x[0] not in exceptions]
    errors = [x for x in findings if x[1] == "ERROR" or (strict and x[1] == "WARN")]
    for rule, level, path, line, msg in sorted(findings, key=lambda x: (x[1] != "ERROR", x[0], x[2], x[3])):
        where = f"{path}:{line}" if line else path
        print(f"{level:5} {rule:8} {where}  {msg}")
    note = f", {len(exceptions)} recorded exception(s)" if exceptions else ""
    print(f"GHOBS check: {len(findings)} finding(s), {len(errors)} blocking{note}")
    return 0 if (warn_only or not errors) else 1

# ---------------------------------------------------------------- sync

def upsert_block(path, block, header=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else header
    start = BEGIN_RE.search(old)
    end = old.find(END, start.end()) if start else -1
    if start and end != -1:
        new = old[:start.start()] + block + old[end + len(END):]
    else:
        new = old.rstrip("\n") + ("\n\n" if old.strip() else "") + block + "\n"
    if not path.exists() or new != old:
        path.write_text(new, encoding="utf-8", newline="\n")
        return True
    return False


def ensure_import(path, line):
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in old:
        return False
    path.write_text((old.rstrip("\n") + "\n" if old.strip() else "") + line + "\n", encoding="utf-8", newline="\n")
    return True


def copy_if_changed(src, dst, overwrite=True):
    if dst.exists() and (not overwrite or dst.read_bytes() == src.read_bytes()):
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True


def run_sync(root, standard_dir, init=False):
    root, std = Path(root).resolve(), Path(standard_dir).resolve()
    version = (std / "VERSION").read_text(encoding="utf-8").strip()
    body = (std / "templates" / "agents-block.md").read_text(encoding="utf-8").strip()
    block = f"<!-- GHOBS:BEGIN v{version} -->\n{body}\n{END}"
    done = []
    if upsert_block(root / "AGENTS.md", block, "# AGENTS.md\n"):
        done.append("AGENTS.md")
    for name in ("CLAUDE.md", "GEMINI.md"):
        if ensure_import(root / name, "@AGENTS.md"):
            done.append(name)
    if upsert_block(root / ".github" / "copilot-instructions.md", block):
        done.append(".github/copilot-instructions.md")
    cursor_header = "---\ndescription: Good Heart Open Build Standard\nalwaysApply: true\n---\n\n"
    if upsert_block(root / ".cursor" / "rules" / "ghobs.mdc", block, cursor_header):
        done.append(".cursor/rules/ghobs.mdc")
    for src, dst in ((std / "scripts" / "ghobs.py", root / ".ghobs" / "ghobs.py"), (std / "versions.yml", root / ".ghobs" / "versions.yml"), (std / "VERSION", root / ".ghobs" / "VERSION")):
        if copy_if_changed(src, dst):
            done.append(str(dst.relative_to(root)))
    for name in ("ghobs-check.yml", "ghobs-sync.yml"):
        if copy_if_changed(std / "templates" / "workflows" / name, root / ".github" / "workflows" / name, overwrite=False):
            done.append(f".github/workflows/{name}")
    if init and copy_if_changed(std / "templates" / "app.yml", root / "app.yml", overwrite=False):
        done.append("app.yml")
    print(("GHOBS sync updated: " + ", ".join(done)) if done else "GHOBS sync: already up to date")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="GHOBS check and sync")
    sub = parser.add_subparsers(dest="cmd", required=True)
    chk = sub.add_parser("check")
    chk.add_argument("--path", default=".")
    chk.add_argument("--site-root", type=Path, help="local rendered output directory for a website: public app")
    chk.add_argument("--warn-only", action="store_true", help="report but never fail (advisory rollout)")
    chk.add_argument("--strict", action="store_true", help="treat warnings as failures")
    syn = sub.add_parser("sync")
    syn.add_argument("--path", default=".")
    syn.add_argument("--standard-dir", required=True)
    syn.add_argument("--init", action="store_true", help="also create app.yml if missing")
    args = parser.parse_args(argv)
    if args.cmd == "check":
        return run_check(args.path, args.warn_only, args.strict, args.site_root)
    return run_sync(args.path, args.standard_dir, args.init)


if __name__ == "__main__":
    sys.exit(main())
