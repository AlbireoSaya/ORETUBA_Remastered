# 2026-10-16 对于GitHub CLI便携安装的修改

- Issue：ISSUE-20261016-01 ｜ 工具安装工程 ｜ issue/ISSUE-20261016-01-gh-install → main
- root：官方来源核验、平台下载部署、验证、批次复核、Git行政与记录；editor-easy DeepSeek/high：两个便携启动脚本。research/editor-hard/reviewer未调用。

## 任务目的

用户要求安装gh。游戏工程及原生goal保持paused；本次仅安装官方GitHub CLI，未恢复游戏攻坚、未登录账号、未上传项目。不涉及游戏条目，不创建虚构作品skill或改Galgame索引。

## 改动清单

- 官方Windows x64 GitHub CLI 2.102.0便携版落在工作区工具/github-cli/2.102.0/bin/gh.exe，下载ZIP亦只落工具/github-cli/。
- 工具/github-cli/gh.cmd封装版本程序与参数透传，GH_CONFIG_DIR及XDG_CACHE_HOME/STATE_HOME/DATA_HOME均在便携目录内，仅setlocal子进程生效；关闭自动更新提示。工具/github-cli/enable-gh.ps1仅为当前PowerShell进程添加wrapper目录到PATH，不修改用户/系统PATH、注册表或PowerShell profile。
- 两个脚本的准确源码存.codex/tools/github-cli/launchers.json；验证/哈希存同目录installation.json。二进制及工具目录被忽略，不入Git。
- 新终端从工作区运行：. "./工具/github-cli/enable-gh.ps1"，之后可运行gh --version；也可直接 & "./工具/github-cli/gh.cmd" --version。不会自动给其他新终端或其他应用增加PATH。

## 验证方式与结果

来源https://github.com/cli/cli/releases/tag/v2.102.0，官方asset gh_2.102.0_windows_amd64.zip。SHA-256 ae64e556ecc240b200f7eba60d550e4bb60d78e860e69dd88c449405b86067f4与官方下载列表一致；解压exe SHA-256 756724853cc579510b58e65e7a7429ad6b1af29cf99ef19b3a95f3b701c5c580。

在当前Windows x64、含空格与中文的工作区路径实测：通过enable脚本后Get-Command gh准确指向工具/github-cli/gh.cmd；gh --version exit0，输出gh version 2.102.0 (2026-09-30)；gh help repo exit0；非法子命令exit1，证明wrapper保持错误退出码；gh auth status --hostname github.com exit1，确认尚未登录。未保存或显示token、用户名/认证原始输出。

## 风险、警示与未完成项

无系统安装、无全局PATH修改，需新终端加载启用脚本；本次不授权登录/建库/推送。日后若登录、扩展或使用外部程序，需继续遵守工作区写入边界；这些脚本不构成OS sandbox。GitHub未登录API触发共享IP限流，已改官方Release直链下载；首版派单误用不存在的GH_CACHE_DIR，root根据官方go-gh配置源码及二进制检查发现，editor修订为真实支持的XDG变量后才部署，首版未应用。第一次help验证因Select-Object -First截断管道使进程遇到提前关闭，不是CLI安装失败；改完整捕获输出再检查退出码后通过。

安装包与来源、源码及哈希可供复核。回滚只需在关闭使用它的终端后删除工作区工具/github-cli便携目录，历史记录保留；当前没有执行删除。新安装尚未验证其他Windows版本或GitHub网络登录。原工程未提交的控制流批次保持原状，没有纳入本次提交。

## 审查结论

root统一复核官方包SHA、两个editor脚本和上述命令结果，通过。仅两个源码/回执JSON与本记录入库；在独立稀疏worktree的issue分支准备全部文档，提交前显式检查分支，通过后合main并离开main。不在main补写文档；真实提交/合并hash以Git日志为准。原工程内容哈希在行政整合前后比较，保持不变；游戏goal继续paused。
