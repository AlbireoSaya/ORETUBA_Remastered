# 阶段163–169 交付说明（扁平布局，无 receipts/ 与 source/ 子目录）

## 范围
仅覆盖阶段163–169。169已终态：exit0、80轮、worker30324、errors[]、parentfail0、hostcleanup passed；source169-summary.json已落stage。168与169均为有界负例；因未确认S00文件SHA同一性，不报完成。163–168证据与限制保留，路径保持扁平。

## 架构
- 新字符串桥：source164新桥对n41读取offset 0x0..0x1A（27字节含NUL）后停止；guestdst为decimal 124081448（0x7655528），src为decimal 143478978（0x88d50c2）；返回原dst，desthash 464c1de27fe392ad541c986d77b2b89b3ec871498dc5b91312bbda80431d9c54与163相同。27字节读仅属164新桥，不属163旧桥。source163 caller为0x43FAC0，this+0x64A8，push 0x29，IAT 0x518188，call 0x43FAD1，return 0x43FAD7。
- 有限输入维护：source164 40轮无error，不代表全作。input device为0x071CE080，offset 0x14: 0x10 -> 0；source 0x458FD9的AND与0x45900A的XOR之byte4由worker 25240操作；main 1836发up24=0；41条源写，非菜单消费证明。source165 actualForeground BOOL 1 / error 0，四次title fullRGB 0但最终白色fullRGB 0，hash 680a1c22a8e114ea0c637847e8cc506794073a55f4350364c8a0421e7dbcc8f0，非对白。
- native style双架构：style getter/setter仅-16 / -20 DWORD；seedsource error 77且restorecaller 99。32/64 nativeSet/get readback；WM_STYLECHANGING/CHANGED 8字节结构允许改new / 只读；destroyHWND actual 0 / error 1400；contract 30非法参数拒绝。API均为实际原系统调用；source setter未来on main调度不等于actual worker API。main style API调度为实际on creator main而非原worker，源回调必须真实执行。

## 168–169负例
source168终态：80 parentrounds，worker_errors[]，root parent failures 0，host-fixture-cleanup passed；6次registered扫描10/20/40/60/80/81全无magic；style getter/setter原调用0，lstrcpynA原调用0；actualSetForegroundWindow BOOL0 / error0 / actual_foreground_is_owned false，保留真实OS拒绝（不凭此单因果断定）。source166 74/80轮停止GetWindowLongA -16 0x40D16D rootadapter assert，workererrors[]，仅magic TOB0、注册长度1347字节（十进制） / registered 0x82D4080不足同一性。source167 getter接续后setter -16 value 348782592 return 4247943 decimal边界assert，无最终threadprefix报告，不假报cleanup。
source169终态：exit0、80轮、worker30324、errors[]、parentfail0、hostcleanup passed；source169-summary.json已落stage。两次actualSetForegroundWindow BOOL0、error0、foregroundowned false；第二次START三个ownedPostMessage在45/46/47轮真实发出，cursor期间用户另行移动则保留用户位置，不强行恢复。6次registered heap头扫描全部无magic。style getter/setter原调用0、lstrcpynA原调用0。未确认S00文件SHA同一性，不报完成。

## 文件与配方
SDK 9 + selftest 6 = 15工程文件，32/64全部6 selftest通过；stylehighbit 32/64实际通过：sdk-style-highbit-32.json / sdk-style-highbit-64.json。
现有文件：sdk-string-32.json、sdk-string-64.json、sdk-style-full-32.json、sdk-style-full-64.json、sdk-phase-integrated-32.json、sdk-phase-integrated-64.json；source163-late-derived.json至source166-late-derived.json、source168-summary.json（root从本地终态导出）、source169-summary.json（已落stage）；root-source-integrity.json；source-string-caller-exact-metadata.json；source-input-latch-metadata.json；canonical167.stderr.txt；candidate-provenance.json；case165-actual-window.png、actual-window-readback-after-parent-BGRX-165.png。
配方 verify-original-style-callback-and-script-hash-06.txt 与 verify-original-delayed-start-retry-07.txt 依赖旧本地ignored缓存，非standalone。

## 未完成、边界与下一路径
- 四版100%、目标TJS、全路线画音未完成；OTV MAGES任务为DSL+CRI，非Lucifen。
- 源163–166完整trace在ignored临时，stage仅摘要与SHA定位，不能称已copy fulltrace。
- 原完整性新验：1 EXE、8 LPK、3 DLL、2 ref、446 SCRIPT、418 IR USERCFG 111未变。原PE仅Unicorn无OS load；原作剧本 / 素材 / PE字节 / 密钥未外发。
- 下一有限路径：前台资格未满足则避免80轮重复空转；同时独立并行推进TOB已有IR/原VM轨迹到目标TJS的覆盖与未知拒绝契约、代表性演出/音频语义。R当前GUI输入路线保留未验证，禁止伪造源foreground或成功。
- 所有新文件由editor-easy产出、root批审 / OS验证配方；root制作OS验证配方不算editor工程实现。