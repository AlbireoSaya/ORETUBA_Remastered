"""Run editor-easy in an isolated Command Code Codex CLI session (Python 3.11+)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import tomllib
import urllib.parse

ROOT = Path(r"E:\ZCode Workspace\Galgame")
SOURCE_CONFIG = Path(r"D:\CodexData\.codex\commandcode.config.toml")
GLOBAL_CONFIG = Path(r"D:\CodexData\.codex\config.toml")
ROLE_CONFIG = ROOT / ".codex" / "agents" / "editor-easy.toml"
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def workspace_path(value: str | Path, *, file: bool = False, directory: bool = False) -> Path:
    """Reject both outside paths and symlink/junction ancestors before resolving."""
    path = Path(os.path.abspath(value))
    try:
        path.relative_to(ROOT)
    except ValueError:
        raise ValueError("路径必须在固定 Galgame 工作区内") from None
    for component in (path, *path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & REPARSE:
            raise ValueError("路径及祖先不得包含符号链接、junction 或其他 reparse point")
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        raise ValueError("解析后路径越出工作区")
    if file and not resolved.is_file():
        raise ValueError("输入文件不存在")
    if directory and not resolved.is_dir():
        raise ValueError("工作目录不存在")
    return resolved


def secret_values(provider: dict, env: dict[str, str]) -> list[str]:
    values: list[str] = []
    def collect(value, key=""):
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                collect(child_value, str(child_key))
        elif isinstance(value, str) and re.search(r"token|secret|api.?key|authorization", key, re.I):
            if value:
                values.append(value)
                if value.lower().startswith("bearer "):
                    values.append(value[7:])
    collect(provider)
    env_key = provider.get("env_key")
    if env_key:
        if not env.get(env_key):
            raise ValueError("提供者所需环境凭据未设置")
        values.append(env[env_key])
    for key, value in provider.get("env_http_headers", {}).items():
        if env.get(value):
            values.append(env[value])
    variants = set()
    for value in values:
        variants.update((value, json.dumps(value, ensure_ascii=False)[1:-1],
                         urllib.parse.quote(value, safe=""), urllib.parse.quote_plus(value)))
    return sorted(variants, key=len, reverse=True)


def redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        text = text.replace(secret, "[REDACTED]")
    # Additional protection for accidentally emitted credentials beyond the source table.
    text = re.sub(r"(?i)(Bearer\s+)[^\s\"'<>]+", r"\1[REDACTED]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]{12,}\b", "[REDACTED]", text)
    return text


def toml_scalar(value) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_scalar(item) for item in value) + "]"
    raise ValueError("提供者配置包含不支持的 TOML 值类型")


def toml_document(data: dict) -> str:
    lines: list[str] = []
    def section(table, prefix=()):
        if prefix:
            lines.append("[" + ".".join(json.dumps(key) for key in prefix) + "]")
        for key, value in table.items():
            if not isinstance(value, dict):
                lines.append(json.dumps(key) + " = " + toml_scalar(value))
        for key, value in table.items():
            if isinstance(value, dict):
                lines.append("")
                section(value, (*prefix, key))
    section(data)
    document = "\n".join(lines) + "\n"
    tomllib.loads(document)
    return document


def existing_workspace_policy(global_config: dict) -> dict:
    """Reuse only this root's explicit existing trust and the Windows sandbox choice."""
    root_key = os.path.normcase(os.path.abspath(ROOT))
    matches = [value for key, value in global_config.get("projects", {}).items()
               if os.path.normcase(os.path.abspath(key)) == root_key]
    if not matches or any(value.get("trust_level") != "trusted" for value in matches):
        raise ValueError("固定工作区缺少一致的既有 trusted 配置，不能自行授予信任")
    policy = {"projects": {str(ROOT): {"trust_level": "trusted"}}}
    windows = global_config.get("windows", {})
    if "sandbox" in windows:
        if windows["sandbox"] not in ("elevated", "unelevated"):
            raise ValueError("既有 Windows sandbox 配置不受支持，不能绕过")
        policy["windows"] = {"sandbox": windows["sandbox"]}
    return policy


def stop_tree(process: subprocess.Popen) -> None:
    # taskkill is invoked without a shell and includes children, not just codex.exe.
    if os.name == "nt":
        subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=NO_WINDOW, timeout=30, check=False)
    else:
        process.kill()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=15)


def remove_runtime_tree(path: Path) -> None:
    """Delete only our verified runtime tree; handle Git's Windows read-only packs."""
    workspace_path(path, directory=True)

    def clear_readonly_and_retry(function, value, exc_info):
        target = workspace_path(value)
        if not target.is_relative_to(path):
            raise ValueError("清理回调路径不属于本次 runtime 目录")
        if not target.exists():
            return
        # workspace_path rejects reparse ancestors before chmod; never follow outside links.
        target.chmod(target.stat().st_mode | stat.S_IWRITE)
        function(str(target))

    for attempt in range(3):
        try:
            workspace_path(path, directory=True)
            shutil.rmtree(path, onerror=clear_readonly_and_retry)
            return
        except FileNotFoundError:
            if not path.exists():
                return
            raise
        except PermissionError:
            if attempt == 2:
                raise
            time.sleep(0.2 * (attempt + 1))


class ProcessJob:
    """Closing a Windows job kills remaining CLI descendants, even after root exit."""
    def __init__(self):
        import ctypes
        from ctypes import wintypes
        class Limits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                        ("flags", wintypes.DWORD), ("min_ws", ctypes.c_size_t),
                        ("max_ws", ctypes.c_size_t), ("active", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in
                        ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
        class Extended(ctypes.Structure):
            _fields_ = [("limits", Limits), ("io", IO), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                        ("peak_job", ctypes.c_size_t)]
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.api.SetInformationJobObject.restype = wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = Extended()
        info.limits.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def assign(self, process):
        import ctypes
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--cwd", default=str(ROOT))
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    secrets: list[str] = []
    run_dir = runtime_home = runtime_temp = None
    process = None
    job = None
    writer = None
    readers: list[threading.Thread] = []
    status = {"state": "failed", "model": "deepseek/deepseek-v4.1-flash",
              "provider": "commandcode", "read_only": args.read_only,
              "started_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    messages: list[str] = []
    tool_failures: list[dict] = []
    lock = threading.Lock()
    events = None
    exit_code = 1
    try:
        if os.name != "nt":
            raise ValueError("此桥接针对 Windows，其他系统不支持")
        if args.timeout_seconds < 1:
            raise ValueError("timeout-seconds 必须大于零")
        prompt_path = workspace_path(args.prompt_file, file=True)
        cwd = workspace_path(args.cwd, directory=True)
        target_dir = workspace_path(args.run_dir)
        if target_dir.exists():
            raise ValueError("run-dir 必须是尚不存在的新目录，禁止覆盖")
        # Fail closed for detached HEAD, unknown branch and any main checkout.
        git = subprocess.run(["git", "-C", str(ROOT), "branch", "--show-current"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             creationflags=NO_WINDOW, timeout=20, check=True)
        branch = git.stdout.strip()
        if not args.read_only and not branch.startswith(("issue/", "agent/")):
            raise ValueError("工程执行必须位于主代理指定的 issue/ 或 agent/ 分支")
        # A nested repository cwd would have a different branch and write discipline.
        cwd_git = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace",
                                 creationflags=NO_WINDOW, timeout=20, check=True)
        if Path(cwd_git.stdout.strip()).resolve() != ROOT.resolve():
            raise ValueError("cwd 必须属于 Galgame 仓库，不能是嵌套仓库")
        prompt = prompt_path.read_text(encoding="utf-8-sig")
        if not prompt.strip():
            raise ValueError("派单文件不能为空")
        role = tomllib.loads(workspace_path(ROLE_CONFIG, file=True).read_text(encoding="utf-8"))
        if role.get("model") != status["model"] or role.get("model_provider") != "commandcode":
            raise ValueError("editor-easy 角色模型或提供者与桥接目标不符")
        if role.get("model_reasoning_effort") != "high":
            raise ValueError("editor-easy 必须使用 high 思考强度")
        source = tomllib.loads(SOURCE_CONFIG.read_text(encoding="utf-8-sig"))
        provider = source["model_providers"]["commandcode"]
        inherited_policy = existing_workspace_policy(
            tomllib.loads(GLOBAL_CONFIG.read_text(encoding="utf-8-sig")))
        env = os.environ.copy()
        secrets = secret_values(provider, env)
        cli = shutil.which("codex.exe") or shutil.which("codex")
        if not cli or Path(cli).suffix.lower() != ".exe":
            raise ValueError("PATH 中未找到已安装的 codex.exe")
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        workspace_path(target_dir.parent, directory=True)
        target_dir.mkdir(exist_ok=False)
        run_dir = workspace_path(target_dir, directory=True)
        runtime_home = run_dir / "runtime-home"
        runtime_temp = run_dir / "runtime-temp"
        runtime_home.mkdir()
        runtime_temp.mkdir()
        logs_dir = runtime_home / "logs"
        sqlite_dir = runtime_home / "sqlite"
        logs_dir.mkdir()
        sqlite_dir.mkdir()
        instruction = (role["developer_instructions"] + "\n"
                       "这是独立 CLI 派单，不是原生子代理。当前工程分支为 " + branch + "。\n"
                       "只执行下方派单写明的范围，禁止切换分支、提交、合并，禁止写入工作区外、"
                       "改动原版、备份及由主代理行政收尾的工程记录。未经主代理在派单中明确授权，"
                       "不得修改任一层术语表或操作浏览器、GUI；获得授权后仍须遵守角色职责、"
                       "实际工具能力与平台权限。"
                       "不得把运行时提供者配置或凭据复制到产物或输出。"
                       "未明确的范围和验收要求报告给主代理；不得自行扩大。\n")
        if args.read_only:
            instruction += "本次只读验证：不得创建、修改或删除文件，只在最终回复报告结论。\n"
        config = {key: role[key] for key in (
            "model", "model_provider", "model_reasoning_effort", "model_context_window",
            "model_auto_compact_token_limit", "model_auto_compact_token_limit_scope",
            "model_catalog_json") if key in role}
        config.update({"developer_instructions": instruction,
                       "approval_policy": "never",
                       "sandbox_mode": "read-only" if args.read_only else "workspace-write",
                       "log_dir": str(logs_dir), "sqlite_home": str(sqlite_dir),
                       "check_for_update_on_startup": False,
                       "model_providers": {"commandcode": provider}})
        config.update(inherited_policy)
        status["reused_workspace_policy"] = inherited_policy
        status["requested_parameters"] = {key: config[key] for key in (
            "model", "model_provider", "model_reasoning_effort", "model_context_window",
            "model_auto_compact_token_limit", "model_auto_compact_token_limit_scope",
            "model_catalog_json", "sandbox_mode") if key in config}
        if not args.read_only:
            config["sandbox_workspace_write"] = {"writable_roots": [str(ROOT)],
                                                  "exclude_tmpdir_env_var": True,
                                                  "exclude_slash_tmp": True}
        # Per-child runtime paths; no parent environment or external config mutations.
        env.update({"CODEX_HOME": str(runtime_home), "TEMP": str(runtime_temp),
                    "TMP": str(runtime_temp), "TMPDIR": str(runtime_temp),
                    "PYTHONPYCACHEPREFIX": str(runtime_temp / "pycache"),
                    "XDG_CACHE_HOME": str(runtime_temp / "cache"),
                    "XDG_STATE_HOME": str(runtime_home / "state"),
                    "CARGO_TARGET_DIR": str(runtime_temp / "cargo-target"),
                    "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
        (runtime_home / "config.toml").write_text(toml_document(config), encoding="utf-8")
        events = (run_dir / "events.jsonl").open("w", encoding="utf-8", newline="\n")
        status.update({"branch": branch, "cwd": str(cwd), "state": "running"})

        def consume(pipe, stream):
            try:
                for line in pipe:
                    safe = redact(line.rstrip("\r\n"), secrets)
                    try:
                        event = json.loads(safe) if stream == "stdout" else None
                    except json.JSONDecodeError:
                        event = None
                    record = event if isinstance(event, dict) else {"type": "bridge.output", "stream": stream, "text": safe}
                    with lock:
                        events.write(json.dumps(record, ensure_ascii=False) + "\n")
                        events.flush()
                        if isinstance(event, dict) and event.get("type") in ("item.completed", "item.failed"):
                            item = event.get("item", {})
                            if (event.get("type") == "item.failed" or item.get("status") == "failed" or item.get("error")
                                    or isinstance(item.get("exit_code"), int) and item["exit_code"] != 0):
                                tool_failures.append({"type": item.get("type"),
                                                      "status": item.get("status"),
                                                      "exit_code": item.get("exit_code"),
                                                      "error": item.get("error")})
                            if (item.get("type") == "agent_message" and isinstance(item.get("text"), str)
                                    and item["text"].strip()):
                                messages.append(item["text"])
                        elif isinstance(event, dict) and event.get("type") in ("error", "turn.failed"):
                            tool_failures.append({"type": event.get("type"),
                                                  "error": event.get("error", event.get("message"))})
            except Exception as error:
                with lock:
                    events.write(json.dumps({"type": "bridge.reader_error", "stream": stream,
                                             "error": redact(str(error), secrets)}, ensure_ascii=False) + "\n")
            finally:
                pipe.close()

        command = [cli, "--no-daemon", "exec", "--ephemeral", "--json", "--color", "never", "--sandbox", config["sandbox_mode"],
                   "--cd", str(cwd), "-"]
        job = ProcessJob()
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                                   shell=False, env=env, cwd=str(cwd), creationflags=NO_WINDOW)
        job.assign(process)
        for pipe, stream in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            reader = threading.Thread(target=consume, args=(pipe, stream), daemon=True)
            reader.start()
            readers.append(reader)
        # Avoid command-line prompt and credentials; only the task travels over stdin.
        def send_prompt():
            try:
                process.stdin.write(prompt)
            except Exception as error:
                with lock:
                    status["stdin_error"] = redact(str(error), secrets)
            finally:
                process.stdin.close()
        writer = threading.Thread(target=send_prompt, daemon=True)
        writer.start()
        try:
            returncode = process.wait(timeout=args.timeout_seconds)
            status["returncode"] = returncode
            status["state"] = "completed" if returncode == 0 else "failed"
            exit_code = 0 if returncode == 0 else 1
        except subprocess.TimeoutExpired:
            stop_tree(process)
            status.update({"state": "timed_out", "returncode": process.returncode})
            exit_code = 124
    except KeyboardInterrupt:
        status["state"] = "interrupted"
        exit_code = 130
    except Exception as error:
        status["error"] = redact(str(error), secrets)
        exit_code = 1
    finally:
        if process is not None and process.poll() is None:
            try:
                stop_tree(process)
            except Exception as error:
                status["termination_error"] = redact(str(error), secrets)
                exit_code = 1
        if job is not None:
            job.close()
        if writer is not None:
            writer.join(timeout=10)
        for reader in readers:
            reader.join(timeout=10)
        if any(reader.is_alive() for reader in readers):
            status["reader_error"] = "子进程输出管道未及时结束"
            status["state"] = "failed"
            exit_code = 1
        if status["state"] == "completed" and (not messages or status.get("stdin_error")):
            status["state"] = "failed"
            status["error"] = "CLI 虽成功退出，但没有最终 agent_message 或派单传入失败"
            exit_code = 1
        status["final_message_count"] = len(messages)
        status["tool_failures"] = tool_failures
        status["completion_scope"] = "completed仅表示模型回合与清理完成；工程成果由主代理在大型任务或阶段成果后批次审查。"
        if events and not any(reader.is_alive() for reader in readers):
            events.close()
        cleanup_errors = []
        # Remove credentials first, so unrelated read-only plugin files cannot retain them.
        if runtime_home is not None:
            config_path = runtime_home / "config.toml"
            try:
                verified_config = workspace_path(config_path)
                if verified_config.exists():
                    verified_config.unlink()
            except Exception as error:
                cleanup_errors.append("运行时凭据配置删除失败: " + redact(str(error), secrets))
        for path in (runtime_home, runtime_temp):
            if path is not None and path.exists():
                try:
                    remove_runtime_tree(path)
                except Exception as error:
                    cleanup_errors.append(redact(str(error), secrets))
        status["runtime_removed"] = not cleanup_errors
        if cleanup_errors:
            status["cleanup_errors"] = cleanup_errors
            status["state"] = "failed"
            exit_code = 1
        status["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        if run_dir is not None:
            workspace_path(run_dir, directory=True)
            result = "\n\n".join(messages) or "未取得最终模型回复；请检查 status.json 与脱敏 events.jsonl。\n"
            (run_dir / "result.md").write_text(redact(result, secrets), encoding="utf-8")
            (run_dir / "status.json").write_text(redact(json.dumps(status, ensure_ascii=False, indent=2), secrets) + "\n", encoding="utf-8")
        print(redact(json.dumps(status, ensure_ascii=False), secrets))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
