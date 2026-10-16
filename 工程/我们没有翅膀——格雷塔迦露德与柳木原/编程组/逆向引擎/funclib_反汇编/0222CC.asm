; V=0x222CC  core=0x222CC..0x2232C（8 条）  过程=0x222CC..0x22364（2 块/14 条，段数 1）
; native=[28]
; 内嵌串 core=-
; 库内 CALL -> -
000222CC  MOV           0x0[-] 0x183C6C8[var#853]                ★ V 入口
000222D8  MOV           0x0[-] 0x183C548[var#850]                
000222E4  MOV           0x0[-] 0x183C5C8[var#851]                
000222F0  MOV_D         0x183E1B8[var#905] 0x1860AD0[L_22300]    
000222FC  EQZ           0x0[-] 0x1860ADC[L_2230C]                
00022308  JZ            0x0[-] 0x1860AFC[L_2232C]                
00022314  MOV           0x0[-] 0x183AE18[var#806]                
00022320  MOV           0x0[-] 0x183AF48[var#808]                
0002232C  LEA_STK       0x0[-] 0x1860B20[L_22350]                
00022338  PUSH          0x2[-]                                   
00022340  PUSH          0x0[-]                                   
00022348  CALLNATIVE    0x1D[native#28] 0x0[-] 0x1869F06[str@""] 
00022358  SP_DROP       0x8[-]                                   
00022360  RET                                                    
