; V=0x20A4C  core=0x20A4C..0x20A74（4 条）  过程=0x20A4C..0x20AA4（2 块/9 条，段数 1）
; native=[669]
; 内嵌串 core=-
; 库内 CALL -> -
00020A4C  MOV           0x0[-] 0x183C5C8[var#851]                ★ V 入口
00020A58  MOV_D         0x183E1B8[var#905] 0x185F238[L_20A68]    
00020A64  JZ            0x0[-] 0x185F244[L_20A74]                
00020A70  RET                                                    
00020A74  LEA_STK       0x0[-] 0x185F260[L_20A90]                
00020A80  PUSH          0x6[-]                                   
00020A88  CALLNATIVE    0x29E[native#669] 0x0[-] 0x1869F06[str@""] 
00020A98  SP_DROP       0x4[-]                                   
00020AA0  RET                                                    
