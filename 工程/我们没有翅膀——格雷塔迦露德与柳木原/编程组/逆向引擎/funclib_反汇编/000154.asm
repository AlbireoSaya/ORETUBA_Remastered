; V=0x154  core=0x154..0x1D4（13 条）  过程=0x154..0x1D4（1 块/13 条，段数 1）
; native=[537]
; 内嵌串 core=['']
; 库内 CALL -> ['0x22fdc']
00000154  LD_STK        0x8[-] 0x183C248[var#844]                ★ V 入口
00000160  PUSH          0x6[-]                                   
00000168  LD_STK        0xC[-] 0x183E94C[L_17C]                  
00000174  ADD           0x1[-] 0x0[-] 0x183E958[L_188]           
00000184  PUSH          0x0[-]                                   
0000018C  CALL          0x18617AC[L_22FDC]                       
00000194  SP_DROP       0x8[-]                                   
0000019C  STORE_RETVAL  0x1869F06[str@""]                        
000001A4  LEA_STK       0x0[-] 0x183E990[L_1C0]                  
000001B0  PUSH          0x2[-]                                   
000001B8  CALLNATIVE    0x21A[native#537] 0x0[-] 0x1869F06[str@""] 
000001C8  SP_DROP       0x4[-]                                   
000001D0  RET                                                    
