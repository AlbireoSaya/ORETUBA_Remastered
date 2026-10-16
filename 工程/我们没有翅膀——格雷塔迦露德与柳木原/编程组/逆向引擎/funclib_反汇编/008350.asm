; V=0x8350  core=0x8350..0x8378（4 条）  过程=0x8350..0x83FC（4 块/17 条，段数 1）
; native=[428]
; 内嵌串 core=-
; 库内 CALL -> -
00008350  LD_STK        0xC[-] 0x183BC48[var#832]                ★ V 入口
0000835C  MOV_D         0x183E1B8[var#905] 0x1846B3C[L_836C]     
00008368  JZ            0x0[-] 0x1846B48[L_8378]                 
00008374  RET                                                    
00008378  MOV_D         0x183BD48[var#834] 0x1846B58[L_8388]     
00008384  JZ            0x0[-] 0x1846BAC[L_83DC]                 
00008390  LEA_STK       0x0[-] 0x1846B9C[L_83CC]                 
0000839C  MOV_D         0x183BD48[var#834] 0x1846B7C[L_83AC]     
000083A8  PUSH          0x0[-]                                   
000083B0  LD_STK        0x10[-] 0x1846B90[L_83C0]                
000083BC  PUSH          0x0[-]                                   
000083C4  CALLNATIVE    0x1AD[native#428] 0x0[-] 0x1869F06[str@""] 
000083D4  SP_DROP       0x8[-]                                   
000083DC  LD_STK        0x8[-] 0x1846BBC[L_83EC]                 
000083E8  JZ            0x0[-] 0x1846BC8[L_83F8]                 
000083F4  HALT_OK                                                
000083F8  RET                                                    
