# C0 隔离 TJS2 夹具运行器

只验证指定旧模块在真实 TJS2 解释器中的 mock 夹具行为。通过也不代表画面、影片解码、源侧演出或整作还原通过。本工具不导入构建脚本，不运行共享测试，不装配成品、不复制影片，不操作 GUI。

运行器：`编程组\工具\performance_runtime.py`。需要 Python 3.11+；Windows 运行采用 kill-on-close Job。默认仅准备，必须显式加 `--run` 才启动解释器。`modules.example.json` 指向 09-12 三个旧 worktree 的只读源码；后续修复必须提供另一份 manifest，不能覆盖旧证据或修改历史夹具。

在 `E:\ZCode Workspace\Galgame` 的 PowerShell 中运行：

```powershell
$runner = '工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\工具\performance_runtime.py'
$manifest = '工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\演出链路\隔离夹具\modules.example.json'
$out = 'E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20261010-06\module-c0\cg-new-run'
python -B $runner --workspace-root 'E:\ZCode Workspace\Galgame' --engine '工具\krkrz\krkrz_20171225\tvpwin32.exe' --modules-manifest $manifest --out-root $out --fixture cg --timeout 15
```

真实执行时追加 `--run`。其它夹具使用 `--fixture movie-seq` / `--fixture effects` 并选择新的 out-root。prepare 目录不能复用为 run；每轮都必须使用全新路径。退出码：0＝PREPARED 或 PASS（必须查看 status 区别）；1＝执行夹具 FAIL；2＝参数/路径/输入拒绝。

目录结构：

```text
<out-root>/runtime/game/       源模块、源夹具的逐字节副本及新 startup/config
<out-root>/runtime/savedata/   本轮引擎存档与 krkr.console.log
<out-root>/evidence/           manifest.json、verdict.json、原始日志副本、UTF-8日志、stdout/stderr
```

out-root 仅允许本工作区 `子代理工作区\` 下新目录。拒绝原版/备份/成品、嵌套 worktree、符号链接/junction/reparse 祖先及已存在目录。源码复制总量上限 20 MiB；引擎从只读绝对路径启动，不复制 engine/plugin。每轮 manifest 记录源码源绝对路径、SHA256、字节数、解释器 SHA256、argv、cwd、随机 nonce、预期断言数和超时。

判定同时要求：本轮 fresh log、唯一 nonce BEGIN/VERDICT、旧夹具成功汇总、精确非零断言数、逐条 PASS/OK 数、无 FAIL/异常、引擎退出 0、无 timeout、整个子进程树清理成功。Windows 先挂起创建进程、加入 Job 后恢复，正常退出也清理后代。当前源码预期 CG=62、movie=39、effects=48；movie 旧报告的 40 不适用于实际 TJS 夹具。

输入 manifest 是可信代码配置，不是对任意 TJS 的安全沙箱；操作系统 Job 保证进程树清理，不限制 TJS 文件 API。只运行已派单的受控源码。新启动器读取原有计数器，不改待测 API 或 mock 断言。

自检：

```powershell
python -B '工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\工具\test_performance_runtime.py'
```

所有 unittest 临时文件位于 `子代理工作区\ISSUE-20261010-06\module-c0\unittest\`，其中包含 Windows junction 拒绝、真实父子进程超时清理，以及旧日志/零断言/缺判词/被捕获异常等负控。

2026-10-10 三个旧夹具首轮 FAIL，历史证据见子代理工作区/ISSUE-20261010-06/module-c0/交付.md（保留）；现行分工为 root 研判、editor-easy 修复、root 阶段审查，research 已停用；Win7及其他系统均未测试，且未做视觉验收。
