"""Prepare/run source-only TJS2 fixtures in a fresh private runtime.

No production build imports, shell invocation, shared savedata or GUI automation.
The JSON manifest is a trusted executable-code input, not a sandbox policy.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import time
import uuid

MARKERS = {"cg": "★CGLFIX★", "movie-seq": "★MOVSEQTEST★", "effects": "★M4FX★"}
FILES = {
    "cg": {"ui_scene_layers.tjs", "ui_scene_layers_fixture.tjs"},
    "movie-seq": {"ui_movie.tjs", "ui_movie_seqtest.tjs"},
    "effects": {"ui_stage_effects.tjs", "ui_stage_effects_fixture.tjs"},
}
FORBIDDEN = {"原版", "备份", "成品", ".git"}
MAX_BYTES = 20 * 1024 * 1024
APPROVED_WORKSPACE = Path(__file__).resolve().parents[4]


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def no_links(path):
    """Reject every existing symlink/junction/reparse ancestor, even in-root ones."""
    absolute = Path(os.path.abspath(path))
    for p in (absolute, *absolute.parents):
        try:
            s = p.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
            raise ValueError("reparse/symbolic path rejected: " + str(p))
    return absolute.resolve()


def within(path, root):
    return path == root or root in path.parents


def validate_out(workspace, out):
    root = no_links(workspace)
    if root != no_links(APPROVED_WORKSPACE):
        raise ValueError("workspace-root must be this runner's registered workspace")
    target = no_links(out)
    allowed = root / "子代理工作区"
    if not root.is_dir() or not within(target, allowed) or target == allowed:
        raise ValueError("out-root must be a new directory below workspace/子代理工作区")
    relative = target.relative_to(root)
    if any(p.casefold() in {x.casefold() for x in FORBIDDEN} for p in relative.parts):
        raise ValueError("protected output path")
    for ancestor in (target, *target.parents):
        if ancestor == root:
            break
        if (ancestor / ".git").exists():
            raise ValueError("other worktree output rejected")
    if target.exists():
        raise ValueError("out-root already exists; choose a fresh run directory")
    return root, target


def source_path(value, workspace):
    p = Path(value)
    if not p.is_absolute():
        p = workspace / p
    p = no_links(p)
    if not p.is_file():
        raise ValueError("missing source: " + str(p))
    return p


def read_inputs(workspace, engine, manifest_path, fixture):
    engine = source_path(engine, workspace)
    manifest_path = source_path(manifest_path, workspace)
    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1:
        raise ValueError("modules manifest schema_version must be 1")
    spec = data["fixtures"][fixture]
    expected = spec["expected_assertions"]
    if type(expected) is not int or expected <= 0:
        raise ValueError("expected_assertions must be positive integer")
    sources = []
    names = set()
    for item in spec["files"]:
        name = item["target"]
        if name not in FILES[fixture] or name in names:
            raise ValueError("unexpected/duplicate target: " + str(name))
        names.add(name)
        path = source_path(item["source"], workspace)
        sources.append((path, name))
    if names != FILES[fixture]:
        raise ValueError("required module/fixture pair missing")
    launcher = Path(__file__).resolve().parent.parent / "演出链路" / "隔离夹具" / (fixture + "_startup.tjs")
    sources.append((source_path(launcher, workspace), "startup.tjs"))
    if sum(p.stat().st_size for p, _ in sources) > MAX_BYTES:
        raise ValueError("source budget exceeds 20 MiB")
    return engine, manifest_path, expected, sources


class WindowsJob:
    """A kill-on-close job; child is assigned while suspended (no spawn race)."""
    def __init__(self):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
        self.api.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        class Basic(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", wintypes.DWORD), ("min_ws", ctypes.c_size_t),
                        ("max_ws", ctypes.c_size_t), ("active_limit", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]
        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", ctypes.c_uint64 * 6),
                        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                        ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = Extended()
        info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())

    def attach_resume(self, proc):
        if not self.api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(proc._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        ntdll = ctypes.WinDLL("ntdll")
        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        ntdll.NtResumeProcess.restype = ctypes.c_long
        if ntdll.NtResumeProcess(wintypes.HANDLE(proc._handle)) < 0:
            raise OSError("NtResumeProcess failed")

    def active(self):
        # JOBOBJECT_BASIC_ACCOUNTING_INFORMATION: four int64, four DWORD.
        values = (ctypes.c_uint64 * 6)()
        if not self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(values), ctypes.sizeof(values), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return (ctypes.cast(values, ctypes.POINTER(wintypes.DWORD)))[10]

    def clean(self):
        if not self.api.TerminateJobObject(self.handle, 1):
            return False
        deadline = time.monotonic() + 3
        while self.active() and time.monotonic() < deadline:
            time.sleep(0.02)
        return self.active() == 0

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def execute(argv, cwd, timeout, evidence):
    """Run an argv in a private process group/job, cleaning descendants on every exit."""
    result = {"returncode": None, "timed_out": False, "cleanup_ok": False, "pid": None}
    job = WindowsJob() if os.name == "nt" else None
    proc = None
    env = os.environ.copy()
    env.update(TEMP=str(cwd), TMP=str(cwd), TMPDIR=str(cwd), PYTHONDONTWRITEBYTECODE="1")
    try:
        with (evidence / "stdout.bin").open("xb") as stdout, (evidence / "stderr.bin").open("xb") as stderr:
            proc = subprocess.Popen(argv, cwd=cwd, env=env, shell=False, stdout=stdout, stderr=stderr,
                                    creationflags=0x4 | 0x08000000 if job else 0,
                                    start_new_session=not bool(job))
            result["pid"] = proc.pid
            if job:
                job.attach_resume(proc)
            try:
                result["returncode"] = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                result["timed_out"] = True
    except Exception as exc:
        result["launch_error"] = str(exc)
    finally:
        if proc:
            if job:
                result["cleanup_ok"] = job.clean()
                if proc.poll() is None:
                    proc.kill()  # assignment may have failed before resume
            else:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                result["cleanup_ok"] = True
            proc.wait(timeout=5)
            if result["returncode"] is None:
                result["returncode"] = proc.returncode
        if job:
            job.close()
    return result


def judge(text, fixture, nonce, expected, fresh, process):
    errors = []
    marker = MARKERS[fixture]
    if not fresh:
        errors.append("missing_or_stale_log")
    if text.count("C0_BEGIN " + nonce) != 1:
        errors.append("missing_or_duplicate_fresh_begin")
    records = re.findall(r"C0_VERDICT " + re.escape(nonce) + r" (PASS|FAIL) (\d+)/(\d+)", text)
    checks = 0
    if len(records) != 1:
        errors.append("missing_or_duplicate_verdict")
    else:
        verdict, passed, total = records[0]
        checks = int(total)
        if verdict != "PASS" or int(passed) != expected or checks != expected:
            errors.append("failed_or_incomplete_assertions")
    if fixture == "movie-seq":
        legacy = re.search(r"断言\s+(\d+)\s+项\s*/\s*失败\s+(\d+)\s+项", text)
        if not legacy or (int(legacy[1]), int(legacy[2])) != (expected, 0) or marker + " DONE" not in text:
            errors.append("legacy_movie_summary_mismatch")
        observed = len(re.findall(r"\[MOVSEQTEST\]\s+PASS\b", text))
    elif fixture == "cg":
        legacy = re.search(re.escape(marker) + r" 结果 PASS (\d+) / FAIL (\d+)", text)
        if not legacy or (int(legacy[1]), int(legacy[2])) != (expected, 0):
            errors.append("legacy_cg_summary_mismatch")
        observed = len(re.findall(r"\[CGLAYER\]\[FIX\]\s+PASS\b", text))
    else:
        legacy = re.search(re.escape(marker) + r" PASS (\d+)/(\d+)", text)
        if not legacy or (int(legacy[1]), int(legacy[2])) != (expected, expected):
            errors.append("legacy_effects_summary_mismatch")
        observed = len(re.findall(r"\[FXFIX\]\s+OK\s", text))
    if observed != expected:
        errors.append("assertion_record_count_mismatch")
    if re.search(r"\bFAIL\b(?!\s+0\b)|C0_EXCEPTION|exception\s+occur|syntax error|\[ERR\]|★FAIL|语法有误|未找到 Member", text, re.I):
        errors.append("failure_or_exception_in_log")
    if process.get("timed_out"):
        errors.append("timeout")
    if not process.get("cleanup_ok"):
        errors.append("process_cleanup_failed")
    if process.get("returncode") != 0 or process.get("launch_error"):
        errors.append("engine_exit_failed")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "assertions": checks, "observed_assertion_records": observed, "expected_assertions": expected}


def write_json(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--modules-manifest", required=True, type=Path)
    parser.add_argument("--out-root", required=True, type=Path)
    parser.add_argument("--fixture", choices=MARKERS, required=True)
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--run", action="store_true", help="explicitly launch the real interpreter")
    args = parser.parse_args(argv)
    try:
        if not math.isfinite(args.timeout) or not 0 < args.timeout <= 60:
            raise ValueError("timeout must be finite, >0 and <=60 seconds")
        workspace, out = validate_out(args.workspace_root, args.out_root)
        engine, input_manifest, expected, sources = read_inputs(workspace, args.engine, args.modules_manifest, args.fixture)
        out.parent.mkdir(parents=True, exist_ok=True)
        no_links(out.parent)
        out.mkdir()  # exclusive: never refresh/reuse an existing run
        runtime = out / "runtime"
        game = runtime / "game"
        savedata = runtime / "savedata"
        evidence = out / "evidence"
        for directory in (game, savedata, evidence):
            directory.mkdir(parents=True)
        nonce = uuid.uuid4().hex
        provenance = []
        for source, name in sources:
            payload = source.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            with (game / name).open("xb") as f:
                f.write(payload)
            provenance.append({"source_readonly_absolute": str(source), "target": name,
                               "sha256": digest, "bytes": len(payload)})
        (game / "config.tjs").write_text('var C0Nonce = "' + nonce + '";\n', encoding="utf-8")
        command = [str(engine), str(game), "-datapath=" + str(savedata) + os.sep,
                   "-readencoding=UTF-8", "-startup=startup.tjs", "-userconf=no"]
        manifest = {"schema_version": 1, "fixture": args.fixture, "nonce": nonce,
                    "engine": str(engine), "engine_sha256": sha(engine), "argv": command,
                    "cwd": str(runtime), "expected_assertions": expected, "sources": provenance,
                    "input_manifest": str(input_manifest), "input_manifest_sha256": sha(input_manifest),
                    "mode": "run" if args.run else "prepare", "timeout": args.timeout,
                    "scope": "TJS2 mock fixture only; no visual or original-performance acceptance"}
        write_json(evidence / "manifest.json", manifest)
        verdict = {"status": "PREPARED", "assertions": 0, "expected_assertions": expected}
        if args.run:
            started_ns = time.time_ns()
            process = execute(command, runtime, args.timeout, evidence)
            log = savedata / "krkr.console.log"
            fresh = log.is_file() and log.stat().st_mtime_ns >= started_ns
            raw = log.read_bytes() if log.is_file() else b""
            text = raw.decode("utf-16", errors="replace") if raw.startswith(b"\xff\xfe") else raw.decode("utf-16-le", errors="replace")
            (evidence / "krkr.console.log").write_bytes(raw)
            (evidence / "console.utf8.txt").write_text(text, encoding="utf-8")
            verdict = judge(text, args.fixture, nonce, expected, fresh, process)
            verdict.update(process=process, fresh_log=fresh, raw_log_sha256=hashlib.sha256(raw).hexdigest())
        write_json(evidence / "verdict.json", verdict)
        print(json.dumps({"out_root": str(out), **verdict}, ensure_ascii=False))
        return 0 if verdict["status"] in ("PASS", "PREPARED") else 1
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REJECTED", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
