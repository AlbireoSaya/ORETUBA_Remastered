# R_完整SOB发布与释放证据_20261012

## 目的
本批次最终技术证据与执行说明，供root验证并应用Git；编辑器侧负责实现，不Git、不改他文件；不含原作源字节外发。

## 已验证要点
原始控制器ctor41B3D0/dtor41B490经malloc50577F/HeapAlloc，栈容量为0x4000（十六进制，即16384个32位字）；实际3子注册加806原始块40E95C..410F2D生成809有序槽、803唯一处理器，精确静态调用顺序。具名向量3：基控制器+DC、ScriptBootFlg +10C、retAppProc +110。USER_VAR.SOB 768记录/3724字节/3数组/2局部重定位，live/快照三数据集等于独立参考。FUNC_LIB.SOB/SOB2经4A6D90加载发布；21 SOB0经4A7000；22容器共42690重定位、607129正文；4A7230弹出释放；删除控制器/归档析构释放全部块与句柄。有效完整4A67E0路径使用两零字节/u16模块数0夹具EMPTY_SOB_METADATA.DAT（sha256 96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7），非原始SOB_INIT.DAT。通用ASCII只读桥CreateFileA/GetFileSize NULL高；基只读API复用；GlobalFree亦调原生RA4F8687。Host64/guest镜像独立，CPU原始x86非原OS启动，宿主10.0.22621 CPython清单，Win7未测。

## 边界
请求SCRIPT/SOB_INIT.DAT缺失，原C++ RaiseException E06D7363/不可续flags1/3参数/magic19930520/3 SEH帧仅捕获STOP；未派发异常，非成功/非noop，原始boot未证明。合成元数据仅验证有效输入路径；非空模块元数据与原始缺失异常路径未验证。provider/list/prefix/cache0/localaux/preopened SCRIPT受控。VM/原生体/渲染/音频/四版本100%仍待办，勿缩目标。

## 并行校验
verify-controller.txt、verify-exception-boundary.txt、verify-sob-publication.txt、verify-ascii-api.txt；JSON对：controller-ctor-summary.json/controller-ctor-API-results.json、missing-initialization-exception-summary.json/missing-initialization-API-results.json、sob-publication-summary.json/sob-publication-API-results.json、ascii-api-fixtures.json。成功API夹具6/拒绝28。
