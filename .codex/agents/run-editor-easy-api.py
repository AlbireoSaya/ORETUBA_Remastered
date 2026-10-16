#!/usr/bin/env python3
# run-editor-easy-api bridge (part 1/3): legacy import + connection config loader.
import argparse, hashlib, importlib.util, json, os, subprocess, sys, tomllib
import urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(r"E:\ZCode Workspace\Galgame")
LEGACY_PATH = ROOT / ".codex/agents/run-editor-easy.py"
DEFAULT_CONFIG = Path(r"D:/CodexData/.codex/commandcode.config.toml")
PROTOCOL = "responses"
REQUIRED_EFFORT = "high"
_PLACEHOLDERS = ("replace", "placeholder", "your_", "your-", "changeme", "example",
                 "xxx", "<key", "todo", "none")


def _load_legacy():
    spec = importlib.util.spec_from_file_location("run_editor_easy_legacy", LEGACY_PATH)
    if spec is None or spec.loader is None:
        raise ValueError("legacy module unavailable: %s" % LEGACY_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_LEGACY = _load_legacy()
workspace_path = _LEGACY.workspace_path
redact = _LEGACY.redact


def _pick(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _as_table(value):
    return value if isinstance(value, dict) else {}


def _validate_endpoint(endpoint):
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("endpoint must be an absolute HTTPS URL")
    if "@" in parsed.netloc:
        raise ValueError("endpoint must not carry username or password")
    if parsed.query or parsed.fragment:
        raise ValueError("endpoint must not carry query or fragment")
    return endpoint


def load_connection(path=None):
    config_path = Path(path) if path is not None else DEFAULT_CONFIG
    if not config_path.is_file():
        raise ValueError("config file not found: %s" % config_path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    providers = _as_table(raw.get("model_providers"))
    section = _as_table(providers.get("commandcode"))
    api_key_env = _pick(section.get("api_key_env"), raw.get("api_key_env"))
    env_key = os.environ.get(api_key_env) if api_key_env else None
    endpoint = _pick(section.get("base_url"), raw.get("endpoint"), raw.get("base_url"))
    api_key = _pick(env_key,
                    section.get("experimental_bearer_token"),
                    section.get("api_key"),
                    raw.get("api_key"),
                    raw.get("experimental_bearer_token"))
    model = _pick(raw.get("model"), section.get("model"))
    effort = _pick(raw.get("model_reasoning_effort"), section.get("reasoning_effort"),
                   raw.get("reasoning_effort"), REQUIRED_EFFORT)
    window = _pick(raw.get("model_context_window"), section.get("context_window"),
                   raw.get("context_window"))
    protocol = _pick(section.get("protocol"), raw.get("protocol"), PROTOCOL)
    if endpoint is None:
        raise ValueError("endpoint is required")
    if api_key is None or any(token in str(api_key).lower() for token in _PLACEHOLDERS):
        raise ValueError("api_key is missing or still a placeholder")
    if model is None or not str(model).strip():
        raise ValueError("model is required")
    if str(effort).strip().lower() != REQUIRED_EFFORT:
        raise ValueError("reasoning_effort must be %r" % REQUIRED_EFFORT)
    if protocol != PROTOCOL:
        raise ValueError("unsupported protocol: %s" % protocol)
    try:
        window = int(window)
    except (TypeError, ValueError):
        raise ValueError("context_window must be a positive integer")
    if window <= 0:
        raise ValueError("context_window must be a positive integer")
    return {
        "endpoint": _validate_endpoint(str(endpoint).rstrip("/")),
        "api_key": str(api_key),
        "model": str(model).strip(),
        "reasoning_effort": REQUIRED_EFFORT,
        "context_window": window,
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # Refuse every HTTP redirect so Authorization is never re-sent to a new target.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_job(cfg, prompt, inputs, allowed, max_tokens, timeout):
    key = str(cfg.get("api_key") or "")
    allowed = [str(p) for p in (allowed or [])]
    inputs = {str(k): str(v) for k, v in (inputs or {}).items()}
    text = json.dumps({"task": prompt, "input": inputs, "allowed": allowed},
                      ensure_ascii=False, separators=(",", ":"))
    if key and key in text:
        raise ValueError("credential present in assembled input")
    size = len(text.encode("utf-8"))
    if size > 3 * 1024 * 1024 or size + int(max_tokens) > int(cfg["context_window"]):
        raise ValueError("request exceeds input or context budget")
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"files": {"type": "array", "items": {
                  "type": "object", "additionalProperties": False,
                  "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                  "required": ["path", "content"]}}, "report": {"type": "string"}},
              "required": ["files", "report"]}
    body = {"model": cfg["model"], "input": text,
            "reasoning": {"effort": cfg["reasoning_effort"]},
            "max_output_tokens": int(max_tokens), "store": False, "stream": True,
            "tools": [{"type": "function", "name": "deliver_files",
                       "description": "Deliver the requested artifacts", "parameters": schema}],
            "tool_choice": {"type": "function", "name": "deliver_files"}}
    req = urllib.request.Request(cfg["endpoint"].rstrip("/") + "/responses",
                                 data=json.dumps(body, ensure_ascii=False).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Accept": "text/event-stream",
                                          "Authorization": "Bearer " + key,
                                          "User-Agent": "GalgameEditorBridge/1.0"})
    event, total = None, 0
    with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as resp:
        while True:
            raw = resp.readline(16 * 1024 * 1024 + 1 - total)
            if not raw:
                break
            total += len(raw)
            if total > 16 * 1024 * 1024:
                raise ValueError("response stream too large")
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            try:
                payload = json.loads(line[5:].strip())
            except ValueError:
                continue
            if payload.get("type") in ("response.completed", "response.failed", "response.incomplete"):
                event = payload
                break
    if not event or event.get("type") != "response.completed":
        raise ValueError("no terminal completed response")
    response = event.get("response") or {}
    if response.get("status") != "completed":
        raise ValueError("terminal response status is not completed")
    calls = [o for o in (response.get("output") or [])
             if o.get("type") == "function_call" and o.get("name") == "deliver_files"]
    if len(calls) != 1:
        raise ValueError("expected exactly one deliver_files call")
    try:
        args = json.loads(calls[0].get("arguments") or "")
    except ValueError:
        raise ValueError("deliver_files arguments are not valid JSON")
    if not isinstance(args, dict) or not isinstance(args.get("files"), list) or not isinstance(args.get("report"), str):
        raise ValueError("malformed deliver_files arguments")
    if not args["files"]:
        raise ValueError("no delivered files")
    data, used = {"files": [], "report": args["report"]}, 0
    for item in args["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("content"), str):
            raise ValueError("malformed file entry")
        used += len(item["content"].encode("utf-8"))
        data["files"].append({"path": item["path"], "content": item["content"]})
    if used > 3 * 1024 * 1024:
        raise ValueError("delivered content exceeds 3 MiB")
    if key and key in json.dumps(data, ensure_ascii=False):
        raise ValueError("credential present in delivered data")
    return data, (response.get("usage") or {})




def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--input-file", action="append", default=[])
    p.add_argument("--allow-write", action="append", default=[], required=True)
    p.add_argument("--connection")
    p.add_argument("--max-output-tokens", type=int, default=32768)
    p.add_argument("--timeout-seconds", type=int, default=600)
    a = p.parse_args()
    if a.max_output_tokens <= 0 or a.timeout_seconds <= 0:
        p.error("--max-output-tokens and --timeout-seconds must be positive")

    root, owned = Path(ROOT), None  # owned = run dir we created ourselves
    try:
        g = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           cwd=str(root), capture_output=True, text=True, shell=False)
        branch = (g.stdout or "").strip()
        if g.returncode != 0 or not branch.startswith(("issue/", "agent/")):
            raise ValueError("branch")

        def wf(v):  # existing file under the workspace, no reparse point
            q = workspace_path(v, file=True)
            if not q.is_file() or q.is_symlink():
                raise ValueError("file")
            return q

        prompt = wf(a.prompt_file)
        inputs = [wf(v) for v in a.input_file]
        conn = wf(a.connection) if a.connection else None

        allowed = {}  # relative posix, casefolded -> absolute Path
        for v in a.allow_write:
            q = workspace_path(v)
            rel = q.relative_to(root)
            if not rel.parts or q.is_dir():  # workspace root or a directory
                raise ValueError("allow")
            if rel.parts[0].casefold() in {".git", "原版", "备份"}:
                raise ValueError("allow")
            if "工程记录" in rel.parts and q.exists():  # only forbid overwriting
                raise ValueError("allow")
            k = rel.as_posix().casefold()
            if k in allowed:
                raise ValueError("duplicate allow")
            allowed[k] = q

        run = workspace_path(a.run_dir)
        rrel = run.relative_to(root).as_posix()
        if not run.is_absolute() or run.exists():
            raise ValueError("run dir")
        if not (rrel.startswith("临时/") or rrel.startswith("子代理工作区/")):
            raise ValueError("run dir")
        for o in [prompt, conn, *inputs, *allowed.values()]:
            if o is None:
                continue
            x, y = os.path.normcase(os.path.abspath(run)), os.path.normcase(os.path.abspath(o))
            if x == y or x.startswith(y + os.sep) or y.startswith(x + os.sep):
                raise ValueError("run dir overlaps")

        cfg = load_connection(str(conn) if conn else None)
        if prompt.stat().st_size + sum(p.stat().st_size for p in inputs) > 3 * 1024 * 1024:
            raise ValueError("input too large")
        raw = prompt.read_bytes()
        blobs = {p: p.read_bytes() for p in inputs}
        if len(raw) + sum(len(b) for b in blobs.values()) > 3 * 1024 * 1024:
            raise ValueError("input too large")
        text = raw.decode("utf-8")  # strict UTF-8, no errors=replace
        texts = {p: b.decode("utf-8") for p, b in blobs.items()}
        key = str((cfg or {}).get("api_key") or "")
        if key and key in text + "".join(texts.values()):
            raise ValueError("secret in input")

        run.mkdir(parents=True, exist_ok=False)  # only after every check passed
        owned = run
        data, usage = request_job(cfg, text, {str(p): t for p, t in texts.items()},
                                  [allowed[k].as_posix() for k in allowed],
                                  a.max_output_tokens, a.timeout_seconds)

        def field(obj, name):
            return obj[name] if isinstance(obj, dict) else getattr(obj, name, None)

        files, report = field(data, "files"), field(data, "report")
        if not isinstance(files, list) or not files or not isinstance(report, str):
            raise ValueError("result")

        def norm(p):
            return str(p).replace("\\", "/").casefold()

        lookup = {norm(q): k for k, q in allowed.items()}
        seen, stage = set(), []
        for it in files:  # validate every returned path before any write
            k = lookup.get(norm(workspace_path(str(field(it, "path")))))
            content = field(it, "content")
            if k is None or k in seen or not isinstance(content, str):
                raise ValueError("result target")
            seen.add(k)
            stage.append((k, content))

        entries = []
        for i, (k, content) in enumerate(stage):  # candidates live only under the run dir
            name = "%04d.txt" % i
            blob = content.encode("utf-8")
            (run / name).write_bytes(blob)
            entries.append({"target": allowed[k].as_posix(), "candidate": name,
                            "sha256": hashlib.sha256(blob).hexdigest()})
        model = str((cfg or {}).get("model") or "")
        (run / "manifest.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        (run / "report.md").write_text(report, encoding="utf-8")
        (run / "status.json").write_text(json.dumps(
            {"status": "staged", "model": model, "reasoning_effort": "high", "usage": usage,
             "candidates": len(entries),
             "disclaimer": "Candidate output only; not review approved."},
            ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    except Exception as e:
        sys.stderr.write(type(e).__name__ + "\n")  # type only: no message, no traceback
        if owned is not None:
            try:
                (owned / "status.json").write_text(json.dumps({"status": "failed"}), encoding="utf-8")
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
