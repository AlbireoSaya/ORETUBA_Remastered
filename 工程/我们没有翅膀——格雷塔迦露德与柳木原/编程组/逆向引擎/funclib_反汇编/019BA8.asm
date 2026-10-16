; V=0x19BA8  core=0x19BA8..0x19C74（17 条）  过程=0x19BA8..0x19C84（3 块/19 条，段数 1）
; native=[253, 252]
; 内嵌串 core=['']
; 库内 CALL -> -
00019BA8  MOV_D         0x183BAC8[var#829] 0x1858388[L_19BB8]    ★ V 入口
00019BB4  JZ            0x0[-] 0x1858450[L_19C80]                
00019BC0  LEA_STK       0x0[-] 0x18583D4[L_19C04]                
00019BCC  MOV           0x183DD38[var#896] 0x18583AC[L_19BDC]    
00019BD8  ADD           0x0[-] 0x0[-] 0x18583BC[L_19BEC]         
00019BE8  MOV_D         0x0[-] 0x18583C8[L_19BF8]                
00019BF4  PUSH          0x0[-]                                   
00019BFC  CALLNATIVE    0xFE[native#253] 0x0[-] 0x18583E8[L_19C18] 
00019C0C  SP_DROP       0x4[-]                                   
00019C14  JZ            0x0[-] 0x1858444[L_19C74]                
00019C20  LEA_STK       0x0[-] 0x1858434[L_19C64]                
00019C2C  MOV           0x183DD38[var#896] 0x185840C[L_19C3C]    
00019C38  ADD           0x0[-] 0x0[-] 0x185841C[L_19C4C]         
00019C48  MOV_D         0x0[-] 0x1858428[L_19C58]                
00019C54  PUSH          0x0[-]                                   
00019C5C  CALLNATIVE    0xFD[native#252] 0x0[-] 0x1869F06[str@""] 
00019C6C  SP_DROP       0x4[-]                                   
00019C74  MOV           0x0[-] 0x183BAC8[var#829]                
00019C80  RET                                                    
