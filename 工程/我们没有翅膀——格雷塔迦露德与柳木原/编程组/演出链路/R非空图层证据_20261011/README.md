# R非空图层合成与未归属对象析构（20261011）

本稿由 editor-easy 提供，可作为证据目录 `README.md`，并追加到 R 作品 skill。root 执行原码核验与 Git；editor 提供独立 reference 代码与知识稿，不宣称整引擎实现完成。产物只暂存后由主代理应用。来源仅为主代理生成的契约元数据，无原游戏脚本、字节或素材。目标四版本 100% 还原尚未完成。

---

## 1. 范围与方法

- 受控环境：在 Unicorn x86-32 中执行原 R EXE + 原 `tvpgl.dll`，原件只读。
- EXE sha256：`b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`。
- 证据路径：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R非空图层证据_20261011/`。
- 新工具：`lucifen_opaque_layers_reference.py`。它是本批交付的独立纯 Python 32bpp opaque fixture oracle，不是 TJS 生产代码。
- 装载事实：10001000 是客体入口地址，不是 GetLibrary 参数；cfg 为 0x98 字节零；手工 map base 10000000，调用实际参数 libobj, cfg。
- 原发布路径：EXE 原 publish block `4A0D91..4A1ABE`，再由原 `48A3F0` 以 `wrapper+4=1` 发布 `5357E4`。未经过 OS 加载 DLL / DllMain，因此不证明原启动 CPU flags。
- 真实全局 `5357E4` 是 TVPGL library wrapper，不是 manager。

---

## 2. ABI 与结构偏移表

| 对象 / 入口 | 偏移 / 地址 | 语义 | 备注 |
|---|---|---|---|
| child 真实构造 | `456800 → base459590 → reset4568D0` | 构造链 | vtable `519854` |
| child visible | byte `+8`，经 `4581E0` | visible 标志 | 受控读取 |
| child enabled | byte `+15`，经 `458260` | enabled 标志 | 受控读取 |
| child id | u32 `+4` | 图层 ID | selector 使用，含高位用例 |
| child sourcebitmap | ptr `+1C` | 源位图指针 | 本批 `alphaFlag=0` |
| child ctor | `+18` | owner 指针 | 观察为 NULL |
| child ctor | `+20` | owned transform 指针 | 观察为 NULL |
| bind | `456910(bitmap, sourceRectPtr=0, x signed32, y signed32)` | 绑定源与坐标 | sourceRectPtr 为 0 |
| 全图 native | `4249E0 → 45AFF0 → child vt+60 = 457900` | 整图合成路径 | 传 NULL clip |
| 分块 native | child vt+64 = `457BD0` | 分块合成路径 | 传 rect clip |
| primary list | aux `+14` | 节点入口 | 受控手工预分配 |
| node | `+0` child，`+1C` next | 链接节点 | 非原插入/排序/归属生命周期 |
| aux+55 | 非零 | 保留既有底图 | 受控分支 |
| aux+56 | 非零 | 跳过 primary | 受控分支 |
| mode | low8 | 0 所有；1 ID 相同；2 ID 不同；其他跳过 | 只取低 8 位 |
| chunkglobal | `529E6D` | 受控 0/1 | 控制整图/分块 |
| 全局 | `5357E4` | TVPGL library wrapper | 不是 manager |

---

## 3. 合成与分块行为

- 整图路径传 NULL clip；分块路径传 rect。
- 宽 320 高 17 实测 clip：`[0,0,320,8]`、`[0,8,320,16]`、`[0,16,320,17]`。
- 每 band 按 node 顺序，两 child 各一 call。
- mode 只取 low8：`0` 所有，`1` ID 相同，`2` ID 不同，其他跳过。
- visible / enabled 非零时进入；`aux+56` 非零跳过 primary；`aux+55` 非零保留既有底图。
- 次列表和 truth gate 未在本批验证。
- 其它宽度阈值只做静态观察，本批不宣称动态覆盖全阈值。

---

## 4. 未归属对象析构

- 析构 6 组 flag：
  - `0`、`2`、`80000000`：正常 `ret`，`eax=child`。
  - `1`、`3`、`80000001`：到原 operator-delete `44B6B0` 入口，stack arg 为 child。
- 仅低 bit 决定 delete 路径。
- 原 vtable 均降为 base `519980`；source 未改。
- free body 不执行。
- owner / owned transform 均为 NULL。
- 因此不证明原 unlink、owner 非空、owned transform 释放或堆 free 成功。

---

## 5. 测试数量与通过口径

- 成功一次单 child 原 DLL pilot，完整 6 个 u32 像素（含高 byte）copy。
- 主 matrix 46 例 = 32 + 9 + 4 + 1：
  - 32：type9/10 × chunk0/1 × order 正常/反向 × dststride 正负 × srcstride 正负。
  - 9：selector（mode / ID 含高位）。
  - 4：flags（hidden / disabled / disableprimary / noclear）。
  - 1：宽 320 高 17。
- 原 child 构造返回 child 指针，bind 返回 0，原 native429 连 compositor/draw 最终返回 0；与独立 oracle 比较 whole buffer 的 source/frame/padding/canary。
- 析构核验 6 组通过。
- `sourcebitmap alphaFlag=0`，opaque blend byte0；不外推 alpha、色键、变换、8bpp、影片/特效、真实场景。

---

## 6. 失败试验与修正

- dummy 空 wrapper 首次导致 `UC_ERR_FETCH_UNMAPPED`，EIP `3866`，无 child draw，未报成功。
- matrix 初次参数 `x=-1` 被 u32 工具 guard 拒；root 将 signed 坐标转 32 位位形后重跑通过。
- destructor 核验初次误用快照字段名导致 `KeyError`；改用已有 `stop_reached` / `stack_words` 后 6 组通过。
- 以上均为 fixture 核验错误，未修改原指令，未填 fake 成功。

---

## 7. 已知边界

- 受控 primary list `aux+14` 节点与 `node+0 child`、`node+1C next` 是手工预分配的链接节点，不是原插入/排序/归属生命周期。
- 次列表和 truth gate 未验证本批。
- 其它宽度阈值只静态观察，本批不宣称动态覆盖全阈值。
- `5357E4` 为 TVPGL library wrapper，不是 manager。
- 未 OS 加载 DLL / DllMain，不证明原启动 CPU flags。
- `alphaFlag=0`、opaque blend byte0；不外推 alpha、色键、变换、8bpp、影片/特效、真实场景。
- 析构仅覆盖低 bit 分支；不证明原 unlink、owner 非空、owned transform 释放或堆 free 成功。
- 目标四版本 100% 还原尚未完成。

---

## 8. 证据文件与复现

- `nonempty-original-compositor-matrix.json`
- `unowned-child-destruction-boundaries.json`
- 单 child pilot 三份：child-ctor-bind-pilot.json、one-child-original-compositor-pilot.json（失败）、one-child-original-DLL-compositor-pilot.json（通过）；其中一次失败。
- opaque-reference-verification.json 含 11 组独立硬编码核验（含错误顺序负控）。
- root 执行收据不是 editor 自验。
- 包内 verify-original-matrix.txt、verify-destruction.txt、verify-reference.txt 可作为 python stdin 命令回放；输出仅工作区临时新目录，且不得覆盖历史。

---

## 9. 下一步

1. 原 primary list 插入/移除与归属。
2. allocator 及原装载路径。
3. alpha / 变换 / 真实脚本状态联动。
4. TJS 接入 + 四版全画音对照。