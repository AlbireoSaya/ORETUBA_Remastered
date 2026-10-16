# R归属列表候选实现知识（editor-easy）

## 范围
证据新目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R归属列表证据_20261011/`；工具`lucifen_owner_list_reference.py`纯fixture oracle非生产。root执行原码核验与批次审查，editor仅交候选实现知识。scope原EXE sha：`b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`。

## 结构
原ctor 459620，owner vt 5199E8；head+4、tail+8、bound+0xC；node 0x24：child+0、dirtyRect+4（受控-1）、key+14、extra+18、prev+1C、next+20；child+18指向owner。旧R非空合成aux+14渲染链node next+1C属不同结构，不等于真实owner列表；本批未跑二者转换/派生。

## 重排459890/4599A0
before_equal/after_equal：thiscall ECX=owner，args child,key32,skip_word；ret 0xC，仅AL是布尔，EAX高位保留原中间值。NULL child或非成员→AL0且不变；skip low8非零且旧key==新key→AL1不动，child mark+9保持0。其它走原unlink/relink，同key分别before `>=`、after `>`，unsigned32比较；原child vfunc+10=458220置byte+9=1，无假回调。

## 矩阵与数量
240原方法完整返回；editor独立reference比较：224=2入口×4选择位置×7新key(0,10,20,25,30,80000000,FFFFFFFF)×4 skipword(0,1,100,10001)，另4 NULL/非成员、12 single。初始key 10,20,20,30；node预分配，child ctor原456800，手工关联owner，原插入未执行。检查全链head/tail/prev/next、key、extra+18、node其它guard、child owner及marks；keys/order输入只读。非成员缺key guard由editor修订并纳入正式复验。

## 插入
4596B0/4597A0共6：NULL child原DWORD1；already-owned原DWORD2；有效owner且child的owner字段+18为NULL时到50577F入口，size0x24；不是ECX owner NULL，不执行allocator，无owner变化。不宣称成功插入或allocator失败3动态验证。

## 移除/清空/析构
459AB0/459670/456850共14：remove NULL/missing真实AL0 return不变；head/middle/tail/single停44B6B0 node free前owner/list/child owner尚未变；clear空list完整return，4节点先清第一个child+18再停node free，其余owner尚不变；owned child析构3位置×flag0/1均先到node free入口、vt已降519980、owner尚未清，未到object free。dirtyRect=-1且bound=0避免原dirty allocator，不外推bound非NULL。

## 交付与命令
固定JSON：owner-original-reorder-matrix.json、owner-insert-allocator-boundaries.json、owner-remove-clear-destructor-boundaries.json。命令verify-reorder.txt/verify-insertion.txt/verify-removal.txt，outputs在workspace临时新目录不得覆盖旧；owner-reference-verification.json 记录10组独立手定期望核验（同键前后、unsigned high key、skip low8、NULL/非成员、缺key拒绝与只读）。

## 局限与下一步
预分配手工owner/node，非原堆、非实际源剧情/notify非NULL/生成渲染列表；无fake HeapAlloc/free或跳过函数填成功。宿主primary启动前置未过，原码仅Unicornguest，不运行OS原EXE/DLL。四版全部剧本/IR/TJS/全画音未完成，goal active。下一步原allocator及owner→render-list派生/更新，再接原VM/TOB资源与TJS忠实剧本。偏移/地址均十六进制。

补充：first综合知识+补丁请求finish length8192，仅405可见tokens，无候选，不作交付。