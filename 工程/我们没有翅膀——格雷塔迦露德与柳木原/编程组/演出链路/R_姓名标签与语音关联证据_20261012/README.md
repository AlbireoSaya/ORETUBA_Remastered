R姓名显示标签与语音条目关联（2026-10-12）

命令25有两个字段：ctx+64D1 长度17（最多16原 bytes）、ctx+64E2 长度16（最多15）。第一字段交给显示对象，vtable 偏移124/128；第二字段与原 VOICE.LPK 文件名匹配。原 labels 只保留 CP932 bytes，不裁决译名，不展开 q/r/运行时变量。静态路径 43F7F0→444740 将目标转写至 +3B8/+3C9 并清空原字段；画面效果尚未验证。

全部 35472 条源记录中：21418 条非空 voice 全部命中原 VOICE.LPK，20319 个不同 stem，14054 条无 voice，0 缺件、0 非 ASCII。VOICE 归档 20418 entries，前后 sha fb9065da961b53b8a0c9d45918349b5787dd0d2d9766d1d9260097490c6b132d；不能把 99 个未直接引用条目称没用。一个原 Ogg 经本地 ffprobe/ffmpeg 无错误，Vorbis 44100Hz 单声道，仅为样本，不是全音频。

35472 原 parser 42FB50→原 dispatcher→完整 43FDA0→42FFF0，共 56590 次真实当前 Windows 宿主 lstrcpynA 调用；目标字段全部 35 bytes，guard、调用帧、source、PE 检查通过。原 x86 ret12 返回 stub 只接宿主真实 API 结果，不做 Python 复制假返回；桥是 host64 ABI，不能称原 x86 kernel、完整 OS，异常或重叠等未证行为不可宣称。25 个 host 边界用例、6 个拒绝。工具 lucifen_host_ansi_bridge.py 由 editor 执行实现、root 验证；派单拆短及源/目标 buffer 修订由 editor 完成。

候选目录 子代理工作区/ISSUE-20261011-02/r-speaker-voice-01/，正式 临时/ISSUE-20261011-02/r-speaker-voice-replay-01/；大 results 忽略，本目录只留摘要、fixtures、消费者指令、recipe 与 root 证据；审查与正式回放以 root 凭据为准。复跑顺序：先 verify-voice-mapping.txt 创建新目录并复制 reference，再 verify-host-fixtures.txt、verify-audio-sample.txt、verify-complete-metadata.txt（后三独立）。PowerShell 在根目录执行 Get-Content -Raw -LiteralPath '<证据>/verify-*.txt' | python -X utf8 -B -；改副本新目录，不改历史。本地成熟 lpk_media 及既有社区 Lucifen-Tools 只 import；ffmpeg/ffprobe 已安装、只读调用，原件不 OS 启动。

缺口仍包括系统 x86 内核、全音频解码/原 native 播放/时序、原 heap 分配、完整字节流/其它 handler、四版本忠实 TJS 与全部帧音频。宿主 primary 前置仍失败，四版完整目标不变。

root行政注记：正式回放已完成，五份完整JSON和reference逐字节一致。14054条“无voice”仅指字段没有语音ID，不能推出静音或停止播放；音频样本只证明本机成熟解码器可解码该条目。本目录为阶段证据，不构成四版全还原验收。
