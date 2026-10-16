; V=0x1FAD4  core=0x1FAD4..0x1FAF0（3 条）  过程=0x1FAD4..0x1FC40（6 块/31 条，段数 2）
; native=[9, 564, 651, 659]
; 内嵌串 core=-
; 库内 CALL -> -
0001FAD4  MOV_D         0x183E1B8[var#905] 0x185E2B4[L_1FAE4]    ★ V 入口
0001FAE0  JZ            0x0[-] 0x185E2C0[L_1FAF0]                
0001FAEC  RET                                                    
0001FAF0  LD_STK        0x8[-] 0x185E2D0[L_1FB00]                
0001FAFC  JZ            0x0[-] 0x185E3C4[L_1FBF4]                
0001FB08  MOV_D         0x183E7B8[var#915] 0x185E2F4[L_1FB24]    
0001FB14  MOV_D         0x183E738[var#914] 0x185E2F8[L_1FB28]    
0001FB20  OR            0x0[-] 0x0[-] 0x185E338[L_1FB68]         
0001FB30  LEA_STK       0x0[-] 0x185E324[L_1FB54]                
0001FB3C  PUSH          0x0[-]                                   
0001FB44  PUSH          0x0[-]                                   
0001FB4C  CALLNATIVE    0xA[native#9] 0x0[-] 0x185E33C[L_1FB6C]  
0001FB5C  SP_DROP       0x8[-]                                   
0001FB64  OR            0x0[-] 0x0[-] 0x185E364[L_1FB94]         
0001FB74  LEA_STK       0x0[-] 0x185E358[L_1FB88]                
0001FB80  CALLNATIVE    0x235[native#564] 0x0[-] 0x185E368[L_1FB98] 
0001FB90  OR            0x0[-] 0x0[-] 0x185E374[L_1FBA4]         
0001FBA0  JZ            0x0[-] 0x185E3C4[L_1FBF4]                
0001FBAC  MOV_D         0x183E138[var#904] 0x185E38C[L_1FBBC]    
0001FBB8  EQZ           0x0[-] 0x185E398[L_1FBC8]                
0001FBC4  JZ            0x0[-] 0x185E3BC[L_1FBEC]                
0001FBD0  LEA_STK       0x0[-] 0x185E3B4[L_1FBE4]                
0001FBDC  CALLNATIVE    0x28C[native#651] 0x0[-] 0x1869F06[str@""] 
0001FBEC  JMP           0x185E40C[L_1FC3C]                       
0001FBF4  LEA_STK       0x0[-] 0x185E3D8[L_1FC08]                
0001FC00  CALLNATIVE    0x294[native#659] 0x0[-] 0x185E3E4[L_1FC14] 
0001FC10  EQZ           0x0[-] 0x185E3F0[L_1FC20]                
0001FC1C  JZ            0x0[-] 0x185E400[L_1FC30]                
0001FC28  JMP           0x185E40C[L_1FC3C]                       
0001FC30  HALT_OK                                                
0001FC3C  RET                                                    
