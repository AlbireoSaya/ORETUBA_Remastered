; V=0x80C8  core=0x80C8..0x80E4（3 条）  过程=0x80C8..0x81C0（4 块/24 条，段数 1）
; native=[721, 721]
; 内嵌串 core=-
; 库内 CALL -> -
000080C8  MOV_D         0x183E1B8[var#905] 0x18468A8[L_80D8]     ★ V 入口
000080D4  JZ            0x0[-] 0x18468B4[L_80E4]                 
000080E0  RET                                                    
000080E4  LD_STK        0xC[-] 0x183B248[var#814]                
000080F0  LEA_STK       0x0[-] 0x18468FC[L_812C]                 
000080FC  MOV_D         0x183B048[var#810] 0x18468DC[L_810C]     
00008108  PUSH          0x0[-]                                   
00008110  LD_STK        0x10[-] 0x18468F0[L_8120]                
0000811C  PUSH          0x0[-]                                   
00008124  CALLNATIVE    0x2D2[native#721] 0x0[-] 0x1869F06[str@""] 
00008134  SP_DROP       0x8[-]                                   
0000813C  MOV_D         0x183B1C8[var#813] 0x184691C[L_814C]     
00008148  JZ            0x0[-] 0x1846970[L_81A0]                 
00008154  LEA_STK       0x0[-] 0x1846960[L_8190]                 
00008160  MOV_D         0x183B148[var#812] 0x1846940[L_8170]     
0000816C  PUSH          0x0[-]                                   
00008174  LD_STK        0x10[-] 0x1846954[L_8184]                
00008180  PUSH          0x0[-]                                   
00008188  CALLNATIVE    0x2D2[native#721] 0x0[-] 0x1869F06[str@""] 
00008198  SP_DROP       0x8[-]                                   
000081A0  LD_STK        0x8[-] 0x1846980[L_81B0]                 
000081AC  JZ            0x0[-] 0x184698C[L_81BC]                 
000081B8  HALT_OK                                                
000081BC  RET                                                    
