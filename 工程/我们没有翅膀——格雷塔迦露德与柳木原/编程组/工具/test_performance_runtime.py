"""Negative controls and real OS process-tree cleanup, all temp files in workspace."""
import importlib.util
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("performance_runtime", Path(__file__).with_name("performance_runtime.py"))
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)
WORKSPACE = Path(__file__).resolve().parents[4]
TEST_ROOT = WORKSPACE / "子代理工作区" / "ISSUE-20261010-06" / "module-c0" / "unittest"
TEST_ROOT.mkdir(parents=True, exist_ok=True)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_ROOT)
        self.root = Path(self.temp.name)
        (self.root / "子代理工作区").mkdir()
        self.policy = patch.object(pr, "APPROVED_WORKSPACE", self.root)
        self.policy.start()

    def tearDown(self):
        self.policy.stop()
        self.temp.cleanup()

    def test_new_path(self):
        target = self.root / "子代理工作区" / "one"
        self.assertEqual(pr.validate_out(self.root, target)[1], target)

    def test_existing_directory(self):
        with self.assertRaises(ValueError):
            pr.validate_out(self.root, self.root / "子代理工作区")
        target = self.root / "子代理工作区" / "one"
        target.mkdir()
        with self.assertRaises(ValueError):
            pr.validate_out(self.root, target)

    def test_outside_and_prefix_sibling(self):
        for target in (self.root.parent / (self.root.name + "-sibling") / "子代理工作区" / "x",
                       self.root / "子代理工作区" / ".." / "outside"):
            with self.assertRaises(ValueError):
                pr.validate_out(self.root, target)

    def test_spoofed_workspace_root(self):
        with self.assertRaises(ValueError):
            pr.validate_out(self.root / "子代理工作区", self.root / "子代理工作区" / "子代理工作区" / "x")

    def test_protected_paths(self):
        for name in ("原版", "备份", "成品", ".git"):
            with self.assertRaises(ValueError):
                pr.validate_out(self.root, self.root / "子代理工作区" / name / "x")

    def test_other_worktree(self):
        tree = self.root / "子代理工作区" / "wt"
        tree.mkdir()
        (tree / ".git").write_text("gitdir: private", encoding="utf-8")
        with self.assertRaises(ValueError):
            pr.validate_out(self.root, tree / "x")

    def test_symlink_or_junction(self):
        dest = self.root / "子代理工作区" / "real"
        dest.mkdir()
        link = self.root / "子代理工作区" / "link"
        if os.name == "nt":
            # Native PowerShell only; no cross-shell filesystem mutation.
            env = os.environ.copy()
            env.update(C0_LINK=str(link), C0_DEST=str(dest))
            result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                "New-Item -ItemType Junction -Path $env:C0_LINK -Target $env:C0_DEST | Out-Null"],
                env=env, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            link.symlink_to(dest, target_is_directory=True)
        with self.assertRaises(ValueError):
            pr.validate_out(self.root, link / "x")
        link.rmdir() if os.name == "nt" else link.unlink()

    def test_prepare_never_launches(self):
        manifest = self.root / "input.json"
        fixture = {"expected_assertions": 1, "files": []}
        for name in pr.FILES["cg"]:
            source = self.root / name
            source.write_text("// sample", encoding="utf-8")
            fixture["files"].append({"source": str(source), "target": name})
        manifest.write_text(json.dumps({"schema_version": 1, "fixtures": {"cg": fixture}}), encoding="utf-8")
        out = self.root / "子代理工作区" / "prepared"
        with patch.object(pr, "execute", side_effect=AssertionError("unexpected launch")):
            self.assertEqual(pr.main(["--workspace-root", str(self.root), "--engine", sys.executable,
                "--modules-manifest", str(manifest), "--fixture", "cg", "--out-root", str(out)]), 0)
        self.assertEqual(json.loads((out / "evidence" / "verdict.json").read_text())["status"], "PREPARED")

    def test_invalid_manifest_rejected_before_write(self):
        manifest = self.root / "invalid.json"
        for fixture in ({"expected_assertions": 0, "files": []},
                        {"expected_assertions": True, "files": []},
                        {"expected_assertions": 1, "files": [{"target": "../escape.tjs", "source": sys.executable}]},
                        {"expected_assertions": 1, "files": []}):
            manifest.write_text(json.dumps({"schema_version": 1, "fixtures": {"cg": fixture}}), encoding="utf-8")
            out = self.root / "子代理工作区" / "rejected"
            self.assertEqual(pr.main(["--workspace-root", str(self.root), "--engine", sys.executable,
                "--modules-manifest", str(manifest), "--fixture", "cg", "--out-root", str(out)]), 2)
            self.assertFalse(out.exists())

    def test_invalid_timeout(self):
        for timeout in ("0", "-1", "nan", "inf", "61"):
            out = self.root / "子代理工作区" / "rejected"
            self.assertEqual(pr.main(["--workspace-root", str(self.root), "--engine", sys.executable,
                "--modules-manifest", str(self.root / "absent.json"), "--fixture", "cg",
                "--out-root", str(out), "--timeout", timeout]), 2)
            self.assertFalse(out.exists())


class VerdictTests(unittest.TestCase):
    def setUp(self):
        self.process = {"returncode": 0, "timed_out": False, "cleanup_ok": True}
        self.text = ("C0_BEGIN abc\n[CGLAYER][FIX] PASS one\n[CGLAYER][FIX] PASS two\n"
                     "★CGLFIX★ 结果 PASS 2 / FAIL 0\nC0_VERDICT abc PASS 2/2\n")

    def result(self, text=None, **kw):
        return pr.judge(self.text if text is None else text, "cg", "abc", 2,
                        kw.get("fresh", True), kw.get("process", self.process))

    def test_positive(self):
        self.assertEqual(self.result()["status"], "PASS")

    def test_missing_verdict(self):
        self.assertEqual(self.result(self.text.replace("C0_VERDICT abc PASS 2/2", ""))["status"], "FAIL")

    def test_stale_log_and_wrong_nonce(self):
        self.assertEqual(self.result(fresh=False)["status"], "FAIL")
        self.assertEqual(self.result(self.text.replace("abc", "old"))["status"], "FAIL")

    def test_zero_or_partial_assertions(self):
        for text in (self.text.replace("PASS 2/2", "PASS 0/0"), self.text.replace("PASS 2/2", "PASS 1/1")):
            self.assertEqual(self.result(text)["status"], "FAIL")

    def test_no_assertion_records(self):
        self.assertEqual(self.result(self.text.replace("[CGLAYER][FIX] PASS", "unrelated"))["status"], "FAIL")

    def test_exception_even_when_caught(self):
        self.assertEqual(self.result(self.text + "==== An exception occured at startup\n")["status"], "FAIL")

    def test_fail_and_duplicate_verdict(self):
        self.assertEqual(self.result(self.text + "FAIL one\n")["status"], "FAIL")
        self.assertEqual(self.result(self.text + "C0_VERDICT abc PASS 2/2\n")["status"], "FAIL")

    def test_timeout_cleanup_and_exit(self):
        for key, value in (("timed_out", True), ("cleanup_ok", False), ("returncode", 1)):
            process = {**self.process, key: value}
            self.assertEqual(self.result(process=process)["status"], "FAIL")

    def test_legacy_mismatch(self):
        self.assertEqual(self.result(self.text.replace("结果 PASS 2", "结果 PASS 1"))["status"], "FAIL")

    def test_movie_and_effect_positive(self):
        movie = "C0_BEGIN abc\n[MOVSEQTEST] PASS: one\n断言 1 项 / 失败 0 项\n★MOVSEQTEST★ DONE\nC0_VERDICT abc PASS 1/1\n"
        effects = "C0_BEGIN abc\n[FXFIX]   OK   one\n★M4FX★ PASS 1/1\nC0_VERDICT abc PASS 1/1\n"
        for fixture, text in (("movie-seq", movie), ("effects", effects)):
            self.assertEqual(pr.judge(text, fixture, "abc", 1, True, self.process)["status"], "PASS")


class ProcessTests(unittest.TestCase):
    def test_timeout_kills_parent_and_child(self):
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            cwd = Path(directory)
            evidence = cwd / "evidence"
            evidence.mkdir()
            script = cwd / "parent.py"
            script.write_text("import subprocess,sys,time\nfrom pathlib import Path\n"
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])\n"
                "Path('child.pid').write_text(str(p.pid))\ntime.sleep(30)\n", encoding="utf-8")
            result = pr.execute([sys.executable, str(script)], cwd, 1.5, evidence)
            self.assertTrue(result["timed_out"])
            self.assertTrue(result["cleanup_ok"], result)
            child_pid = int((cwd / "child.pid").read_text())
            if os.name == "nt":
                api = ctypes.WinDLL("kernel32", use_last_error=True)
                api.OpenProcess.restype = ctypes.c_void_p
                api.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                api.CloseHandle.argtypes = [ctypes.c_void_p]
                handle = api.OpenProcess(0x1000, False, child_pid)
                if handle:
                    code = ctypes.c_ulong()
                    self.assertTrue(api.GetExitCodeProcess(handle, ctypes.byref(code)))
                    api.CloseHandle(handle)
                    self.assertNotEqual(code.value, 259)
            else:
                with self.assertRaises(ProcessLookupError):
                    os.kill(child_pid, 0)


if __name__ == "__main__":
    import ctypes
    unittest.main(verbosity=2)
