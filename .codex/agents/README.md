# Galgame 项目子代理

| 角色 | 状态 | 模型 ID | 提供者 | 思考强度 | 职责 |
| --- | --- | --- | --- | --- | --- |
| editor-easy | 现行 | deepseek/deepseek-v4.1-flash | commandcode | high | 实施全部难度模块：改动、探索、批量处理、文档/数据整理与模块自检 |
| research | 暂停 | gpt-6.1-sol | openai | high | 原职责：只读分析研判与高/中/低难度分级 |
| editor-hard | 暂停 | gpt-6.1-sol | openai | medium | 原职责：仅高难度实施 |
| reviewer | 暂停 | gpt-6.1-sol | openai | high | 原职责：按主代理安排的批次独立审查 |

每份 TOML 的 `name` 是实际角色名；Codex 原生子代理通过 `agent_type` 选择角色，任务的显示名称与角色名是不同参数。配置形式依据 [OpenAI 官方子代理文档](https://learn.chatgpt.com/docs/agent-configuration/subagents)。

## 当前状态

- research、editor-hard、reviewer 暂停：用户显式重新启用前不派发，无在途任务；角色文件保留原 model、provider、思考强度与 sandbox，说明与 developer_instructions 精简为暂停口径，未使用 `enabled = false` 等不受支持的标记。
- editor-easy 为当前唯一实施角色，承接全部难度（含探索、复杂逻辑与跨文件接口），不再按难度升级到上述暂停角色。模型、提供者、high、上下文窗口 1,000,000、自动压缩阈值 800,000、统计范围 `total` 与模型目录等既有键保持不变。
- 本次配置任务不改游戏工程；配置阶段完成后，后续游戏任务按本文件的分工执行。

## 调用 editor-easy（API 桥接，精确用法）

把完整派单写成工作区内 UTF-8 文件，选择尚不存在的运行目录，然后执行：

```powershell
python -X utf8 -B .codex\agents\run-editor-easy-api.py `
  --prompt-file "E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-YYYYMMDD-NN\派单.txt" `
  --run-dir "E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-YYYYMMDD-NN\easy-run-01" `
  --input-file "E:\ZCode Workspace\Galgame\AGENTS.md" `
  --input-file "E:\ZCode Workspace\Galgame\Galgame.md" `
  --allow-write "E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-YYYYMMDD-NN\产物\out.txt"
```

- `--prompt-file`：绝对路径派单文件。
- `--run-dir`：全新目录，不覆盖既有运行目录。
- `--input-file`：显式列出要注入的文件，可重复。
- `--allow-write`：逐个给出精确的允许写入目标，可重复；未列出的路径不写。
- `--connection` 可省略；省略时只读读取既有连接配置。

连接为 HTTPS Responses 接口并流式返回，思考强度 high，上下文为本地配置。密钥、凭据与提示词不写入日志、命令行参数或结果文件，也不进入版本库。

API 桥接的连接参数来自既有提供者配置或 `--connection`，不会自动套用角色 TOML、注入 AGENTS.md 或读取仓库文件。主代理按派单显式提供已批准的适用规范与角色指令；角色 TOML 的原生 / CLI 参数只表示对应通道的配置。新 API 通道为文本批处理，不自动执行工具或压缩会话。

## 暂存与落地

桥接只在运行目录内暂存编号候选文件与 manifest，不自动执行任何命令。主代理（root）审阅候选与 manifest 后，通过真实平台工具落地到目标文件；主代理作为工具操作者按实际权限执行被授权的命令，不代替 editor-easy 做引擎实现。

## 连接配置（手工）

在被忽略的 `临时/editor-easy/connection.toml` 中，按示例 `.codex/agents/editor-easy.connection.example.toml` 手工填写其五个字段。该文件不进入版本库，缺失或字段不全时报告并等待补齐，不凭印象推断连接参数。

## 权限与边界

- 主代理默认最高权限；editor-easy 的 `workspace-write` 只是默认设置，实际权限由主代理按派单与平台可授予能力分配，不绕过系统、工作区外禁写、原版只读与历史产物不覆盖边界。
- 有效权限以平台为准，Python 路径守卫不等同于操作系统沙箱；GUI/浏览器沿用真实工具规则。
- 翻译、校对、润色或术语一致性任务每次须完整读取两层四份规范文件；作品层两份文件绝对路径由主代理在派单中给出。

## 审查与验收

- 主代理负责分析、术语裁决、派单、接收产物与按阶段批次审查，通常不在每个小改动后即时派审。
- 桥接回合完成或退出码 0 只表示已暂存候选与报告，不代表工程通过审查；主代理核对实际产物、验证结果与允许范围后统一收尾，合并、工程记录与索引维护由主代理负责。
- 原生 OpenAI 父会话不能通过角色 `model_provider` 切换提供者；也不声称运行时提供者、原生派发接口或沙箱实现发生变化。

## 目标与检查点

`/goal` 采用有限检查点：以实际证据判定是否完成，不虚报完成，不隐式追加预算；检查点由主代理自主规划；只有用户明确要求时才设置 token 预算。

## 历史记录

- 旧 `run-editor-easy.py` 与 [验证结果_20261010.json](./验证结果_20261010.json) 保留为历史与回退参考，不删除、不追改；旧「主代理技术二审」等措辞已由现行口径替代，不再重复其矛盾描述。
- ISSUE-20261010-03 / 04 / 05 的工程记录保留链接，供追溯角色创建、职责同步与桥接验证的当时事实。

## 本机依赖

- DeepSeek 提供者与模型目录来自本机用户级配置 `D:\CodexData\.codex\commandcode.config.toml` 与 `D:\CodexData\.codex\commandcode-models.json`；复制项目到其他机器时须配置对应依赖。
