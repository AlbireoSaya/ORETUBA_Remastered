; V=0x205D0  core=0x205D0..0x205EC（3 条）  过程=0x205D0..0x20638（2 块/10 条，段数 1）
; native=[669]
; 内嵌串 core=-
; 库内 CALL -> -
000205D0  MOV_D         0x183E1B8[var#905] 0x185EDB0[L_205E0]    ★ V 入口
000205DC  JZ            0x0[-] 0x185EDBC[L_205EC]                
000205E8  RET                                                    
000205EC  LEA_STK       0x0[-] 0x185EDF4[L_20624]                
000205F8  LD_STK        0x8[-] 0x185EDDC[L_2060C]                
00020604  ADD           0x8[-] 0x0[-] 0x185EDE8[L_20618]         
00020614  PUSH          0x0[-]                                   
0002061C  CALLNATIVE    0x29E[native#669] 0x0[-] 0x1869F06[str@""] 
0002062C  SP_DROP       0x4[-]                                   
00020634  RET                                                    
