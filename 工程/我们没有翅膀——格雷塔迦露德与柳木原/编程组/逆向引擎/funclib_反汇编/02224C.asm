; V=0x2224C  core=0x2224C..0x222CC（12 条）  过程=0x2224C..0x222CC（1 块/12 条，段数 1）
; native=[26, 487, 52]
; 内嵌串 core=['']
; 库内 CALL -> ['0x21b50']
0002224C  LEA_STK       0x0[-] 0x1860A40[L_22270]                ★ V 入口
00022258  PUSH          0x2[-]                                   
00022260  PUSH          0x0[-]                                   
00022268  CALLNATIVE    0x1B[native#26] 0x0[-] 0x1869F06[str@""] 
00022278  SP_DROP       0x8[-]                                   
00022280  CALL          0x1860320[L_21B50]                       
00022288  STORE_RETVAL  0x1869F06[str@""]                        
00022290  LEA_STK       0x0[-] 0x1860A74[L_222A4]                
0002229C  CALLNATIVE    0x1E8[native#487] 0x0[-] 0x1869F06[str@""] 
000222AC  LEA_STK       0x0[-] 0x1860A90[L_222C0]                
000222B8  CALLNATIVE    0x35[native#52] 0x0[-] 0x1869F06[str@""] 
000222C8  RET                                                    
