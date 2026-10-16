; V=0x21230  core=0x21230..0x21288（8 条）  过程=0x21230..0x214CC（3 块/16 条，段数 2）
; native=[574, 5]
; 内嵌串 core=['']
; 库内 CALL -> -
00021230  FRAME_ALLOC   0x14[-]                                  ★ V 入口
00021238  MOV_D         0x183C2C8[var#845] 0x185FA18[L_21248]    
00021244  JZ            0x0[-] 0x185FA58[L_21288]                
00021250  MOV           0x0[-] 0x183C2C8[var#845]                
0002125C  LEA_STK       0x0[-] 0x185FA48[L_21278]                
00021268  PUSH          0x1[-]                                   
00021270  CALLNATIVE    0x23F[native#574] 0x0[-] 0x1869F06[str@""] 
00021280  SP_DROP       0x4[-]                                   
00021288  LEA_STK       0x0[-] 0x185FA74[L_212A4]                
00021294  PUSH          0x0[-]                                   
0002129C  CALLNATIVE    0x6[native#5] 0x0[-] 0x185FA88[L_212B8]  
000212AC  SP_DROP       0x4[-]                                   
000212B4  JZ            0x0[-] 0x185FC8C[L_214BC]                
000212C0  HALT_OK                                                
000214BC  SP_DROP       0x14[-]                                  
000214C4  RETVAL_RET    0x0[-]                                   
