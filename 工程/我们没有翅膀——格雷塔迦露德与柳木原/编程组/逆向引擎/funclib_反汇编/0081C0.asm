; V=0x81C0  core=0x81C0..0x81DC（3 条）  过程=0x81C0..0x8218（2 块/9 条，段数 1）
; native=[746]
; 内嵌串 core=-
; 库内 CALL -> -
000081C0  MOV_D         0x183E1B8[var#905] 0x18469A0[L_81D0]     ★ V 入口
000081CC  JZ            0x0[-] 0x18469AC[L_81DC]                 
000081D8  RET                                                    
000081DC  LEA_STK       0x0[-] 0x18469D4[L_8204]                 
000081E8  MOV_D         0x183B048[var#810] 0x18469C8[L_81F8]     
000081F4  PUSH          0x0[-]                                   
000081FC  CALLNATIVE    0x2EB[native#746] 0x0[-] 0x1869F06[str@""] 
0000820C  SP_DROP       0x4[-]                                   
00008214  RET                                                    
