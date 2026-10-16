; V=0x1C3C0  core=0x1C3C0..0x1C3DC（3 条）  过程=0x1C3C0..0x1C43C（3 块/12 条，段数 1）
; native=[208]
; 内嵌串 core=-
; 库内 CALL -> -
0001C3C0  MOV_D         0x183E1B8[var#905] 0x185ABA0[L_1C3D0]    ★ V 入口
0001C3CC  JZ            0x0[-] 0x185ABAC[L_1C3DC]                
0001C3D8  RET                                                    
0001C3DC  MOV           0x0[-] 0x1839E20[var#781]                
0001C3E8  MOV_D         0x183BE48[var#836] 0x185ABC8[L_1C3F8]    
0001C3F4  JZ            0x0[-] 0x185AC08[L_1C438]                
0001C400  LEA_STK       0x0[-] 0x185ABF8[L_1C428]                
0001C40C  MOV           0x183BE48[var#836] 0x185ABEC[L_1C41C]    
0001C418  PUSH          0x0[-]                                   
0001C420  CALLNATIVE    0xD1[native#208] 0x0[-] 0x1869F06[str@""] 
0001C430  SP_DROP       0x4[-]                                   
0001C438  RET                                                    
