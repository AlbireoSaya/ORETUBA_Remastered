; V=0x1C738  core=0x1C738..0x1C790（7 条）  过程=0x1C738..0x1C7C0（3 块/12 条，段数 1）
; native=[537]
; 内嵌串 core=-
; 库内 CALL -> -
0001C738  MOV_D         0x183E1B8[var#905] 0x185AF24[L_1C754]    ★ V 入口
0001C744  MOV_D         0x183E7B8[var#915] 0x185AF28[L_1C758]    
0001C750  OR            0x0[-] 0x0[-] 0x185AF40[L_1C770]         
0001C760  MOV_D         0x183E738[var#914] 0x185AF44[L_1C774]    
0001C76C  OR            0x0[-] 0x0[-] 0x185AF50[L_1C780]         
0001C77C  JZ            0x0[-] 0x185AF60[L_1C790]                
0001C788  RETVAL_RET    0x1[-]                                   
0001C790  LEA_STK       0x0[-] 0x185AF7C[L_1C7AC]                
0001C79C  PUSH          0x0[-]                                   
0001C7A4  CALLNATIVE    0x21A[native#537] 0x0[-] 0x1869F06[str@""] 
0001C7B4  SP_DROP       0x4[-]                                   
0001C7BC  HALT_OK                                                
