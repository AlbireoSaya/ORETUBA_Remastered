# ISSUE-20261011-02 阶段归档与批次审查

2026-10-11，root 集中复核。原始日志、基线备份与候选仍保留在子代理工作区/ISSUE-20261011-02，不覆盖旧成果。本批是基础工具与来源证据归档，四版本忠实剧本及完整演出还原尚未完成。

## 本批通过范围

- C0：performance_runtime.py、自检、三个启动器、示例 manifest 和 README。21 项自检通过，含 Windows junction 拒绝和父子进程超时清理。Job 清理进程树，不提供文件系统沙箱。
- C1：本目录三文件差量补丁、基线与结果哈希、真实运行 verdict。影片回调绑定实例、代次和片段身份，并增加一次性闸；特效夹具使用已有时钟注入口、补全 mock 画布尺寸，保留 48 条行为断言与严格异常判据。movie_late.json 的 41→47 是新增六项断言的行政配置，单列在来源 JSON 中。
- R/OTV：editor-easy 产出的工具 r_source_audit.py、otv_source_audit.py，只读复用 lpk_patch 和 cricodecs。R 446 明文条目全部匹配；OTV 原版 499 项来源现已定位，回收两缺项的回执与哈希留档，原文不进本批 Git。输出 JSON 不代表演出还原。
- 长程计划、索引、工程记录与以下事实证据。

| 范围 | 结果 | verdict |
| --- | --- | --- |
| CG mock | PASS 62/62 | cg-phase-01_verdict.json |
| 影片基础 | PASS 39/39 | movie-base-01_verdict.json |
| 影片输入 | PASS 43/43 | movie-inputs-01_verdict.json |
| 迟到及重复回调 | PASS 47/47 | movie-late-02_verdict.json |
| 修复前影片＋新夹具负控 | FAIL，44 项成功记录/47 项预期 | movie-old-negative-01_verdict.json |
| 特效 mock | PASS 48/48 | effects-02_verdict.json |

原始日志按 verdict 中的 raw_log_sha256 在本机忽略目录核验。严格运行器同时检查 nonce、新日志、退出码、异常、断言数和进程清理。补丁语法用 git apply --numstat 验证；文本补丁使用 LF，应用时先核对原始 SHA256，并保持目标原有 CRLF。不得应用到生产文件或不匹配的基线。

## 复验与范围限制

在工作区根运行：

```powershell
python -X utf8 -B '工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\工具\r_source_audit.py'
```

检查 count=446、每行 match=true、missing/extra 为空。安装介质 SHA256 见 R_原版身份.json，不执行原版 EXE。条目命名清单和逐项哈希已归档，不包含剧本文本。

C0 命令见隔离夹具 README。C1 本机 manifest 为 C1_TJS兼容/modules.c1.json、controls/movie_inputs.json、controls/movie_late.json，每次 --run 使用新的子代理工作区目录。

完整 C1 隔离模块快照本批未入库：此前其他改动以及 B0/B1 产物尚待统一审查。修订补丁的基线备份路径和哈希见 C1_修订来源.json，完整集成与成品接入另批审查，此证据包不能当独立成品。当前影片验证限于既有异步成功、同步失败播放契约，未验证任意同步成功回调。原作画面、影片解码和音频时序未由 mock 证明。

## 下一检查点

R 版已确认 418 TOB、23 SOB、3 DAT、INF/SYS 各一，共 446 条目。旧作品知识的 21 SOB 分类待 editor-easy 增量订正；后续解析以本批安装介质对账为准。分别连接 gameinit/main/func_lib/movieplay/op 与剧情入口，独立核实 R 版 handler 和参数，不套用 OT 编号。

OTV SCRIPT.cpk 实测 499 唯一条目；497 现有文件逐项匹配，缺 adv.txt/scn.txt，已精确回收并验哈希。当前目录的 498 文件还含生成 TSV。回收配置补足五个启动入口、32 个角色定义文件、字幕窗口参数、12 支 Movie 与 8 项 EffectMovie 的源定义；配置不是运行语义证明，别名不得静默去重。之后推进 VM 参数、原作观察、无损剧本编译及画音对照。OTV SELF 加密、OTA 原始身份仍是显式未完成项。

DeepSeek high 在大请求中多次耗尽输出预算而无候选，失败回执保留；后续采用小而完整的代码交付并复用未变规范，减少重复输入。本批未降低指定思考强度，未发送原作剧本、素材、二进制或凭据。
