; V=0x1C8D0  core=0x1C8D0..0x1C8EC（3 条）  过程=0x1C8D0..0x1C93C（2 块/11 条，段数 1）
; native=[57]
; 内嵌串 core=-
; 库内 CALL -> -
0001C8D0  MOV_D         0x183E1B8[var#905] 0x185B0B0[L_1C8E0]    ★ V 入口
0001C8DC  JZ            0x0[-] 0x185B0BC[L_1C8EC]                
0001C8E8  RET                                                    
0001C8EC  LEA_STK       0x0[-] 0x185B0F8[L_1C928]                
0001C8F8  MOV_D         0x183ACB8[var#804] 0x185B0D8[L_1C908]    
0001C904  PUSH          0x0[-]                                   
0001C90C  LD_STK        0xC[-] 0x185B0EC[L_1C91C]                
0001C918  PUSH          0x0[-]                                   
0001C920  CALLNATIVE    0x3A[native#57] 0x0[-] 0x1869F06[str@""] 
0001C930  SP_DROP       0x8[-]                                   
0001C938  RET                                                    
