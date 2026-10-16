; V=0x209A4  core=0x209A4..0x209D0（4 条）  过程=0x209A4..0x20A48（3 块/15 条，段数 1）
; native=[672]
; 内嵌串 core=-
; 库内 CALL -> -
000209A4  MOV           0x0[-] 0x183C5C8[var#851]                ★ V 入口
000209B0  MOV_D         0x183E1B8[var#905] 0x185F190[L_209C0]    
000209BC  JZ            0x0[-] 0x185F1A0[L_209D0]                
000209C8  RETVAL_RET    0x0[-]                                   
000209D0  LD_STK        0x8[-] 0x185F1B0[L_209E0]                
000209DC  EQZ           0x0[-] 0x185F1BC[L_209EC]                
000209E8  JZ            0x0[-] 0x185F1D0[L_20A00]                
000209F4  ST_STK        0x3E8[-] 0x8[-]                          
00020A00  LEA_STK       0x0[-] 0x185F200[L_20A30]                
00020A0C  LD_STK        0x8[-] 0x185F1EC[L_20A1C]                
00020A18  PUSH          0x0[-]                                   
00020A20  PUSH          0x6[-]                                   
00020A28  CALLNATIVE    0x2A1[native#672] 0x0[-] 0x1869F06[str@""] 
00020A38  SP_DROP       0x8[-]                                   
00020A40  RETVAL_RET    0x1[-]                                   
