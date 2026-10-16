# R 原版音频DLL装载与WinMain预初始化证据（20261012）

## 范围与停止点
本批只做原版音频DLL只读装载与WinMain预初始化的可复核证据，不声称完成还原。原ORETUBAR.EXE SHA256 b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33，WinMain 452CF0，真实父构造40A0A0发布530C94=02003000；WinMain参数为guest基址400000、0、空cmdline指针、show10，不是原OS启动。当前精确停止在SHGetSpecialFolderPathA，调用返回地址VA 4711332（十六进制47E3A4，优先用十进制防错），args HWND=0、dst、CSIDL=26、fCreate=1；HWND仍为0，WinMain未返回、原shutdown未执行。

## DLL装载与执行边界
原wuvorbis.dll SHA256 302b1eb97ed0f6110904e84c11bf7436e4cdddd414f4d24d105aba687f32b47f，PE32 base 11000000、size 33000、CRT入口11012DED。只做只读映射与受控Unicorn x86执行，禁止OS装载/执行原EXE与DLL。原CRT attach调用[base,1,0]实际返回1；以本机真实Windows叶API加host64标准结构显式转换为guest32，独立heap/TLS/CS；当前HOST ACP936，宿主命令行/env只进入guest内存，绝不记录或外发内容；guest原模块路径元数据指向备份，不作为安装目录证明。未处理异常过滤器仅纯guest状态、初始0受控，不向OS注册原函数；guestCPU已FNINIT前置，原CRT后FPCW=023F，不构成完整OS loader或Win32原环境证明。attach时86块、1TLS、5CS由原CRT真实产生，不声称原DLL detach已完成。

## 接口与调用
原DLL 40 export；现有工具krkrz/krkrz_20171225/plugin/wuvorbis.dll与公开krkrz/wuvorbis的39接口相符，原版额外GetOptionDesc。DS_SPRITE.DLL与DS_MOVIE.DLL均preferred 60000000、各2 export，未来不能同址装载，重定位未解决；PE32 parser不解析64位插件。WinMain实际LoadLibraryA请求由guest adapter在原DLL attach成功后返回原基址，实际GetProcAddress成功15接口：Query_sizeof_OggVorbis_File、wu_ov_clear、wu_ov_open_callbacks、wu_ov_seekable、wu_ov_pcm_total、wu_ov_time_total、wu_ov_raw_seek、wu_ov_time_seek、wu_ov_raw_tell、wu_ov_pcm_tell、wu_ov_time_tell、wu_ov_info、wu_ov_read、wu_SetCPUType、wu_DetectCPU。query机器码返回704，不超过引擎上限960；DetectCPU与SetCPUType(arg 31129622)实际执行，属Unicorn默认CPU结果，不是原机硬件或PCM证明。

## 初始化数据
WinMain实际只读打开SCRIPT.LPK，读header 8、index 17151；原native资源回退自然缺失SCRIPT/LL_APP.SYS与LL_APP.INF（真CreateFileA error3）后回到归档，实际seek 93617/read 25及seek 93516/read 101。root已复验native-initialization-data.json：原生返回ll_app.sys 25字节、ll_app.inf 101字节，均与既有只读源逐字节相同。为工作区写边界不调用会外部创建目录的API，下一阶段验证只读路径查询与工作区保存路径映射。

## 证据与边界
证据清单固定：WinMain-boundary.json、DLL_API_events.json、DLL-source-inventory.json、helper-delivery-manifest.json、root-source-integrity.json、host-fixture-cleanup.json、verify-WinMain.txt、wuvorbis-shared-setup.txt、verify-source-integrity.txt、root-batch-review.json，并加入native-initialization-data.json与host-leaf-fixtures.json，以正式证据与复核结论为准。公共成熟源码https://github.com/krkrz/wuvorbis，raw master的wuvorbis.def与wuvorbisfile_stub.c为cdecl wrapper直接调libvorbis，仅作ABI复用参考，不证明原版本一致或PCM相同；GetOptionDesc差异下不能直接换DLL。保留全scope OT/OTA/OTV/OTR，忠实TJS与画音全部路线/状态/帧/音频100%未完成，不把文件与接口覆盖当还原率。完整OS级异常过滤器与原环境复刻仍未解决；有限纯guest注册状态已验证，不笼统称其未解决。本批文档不代表git合并。