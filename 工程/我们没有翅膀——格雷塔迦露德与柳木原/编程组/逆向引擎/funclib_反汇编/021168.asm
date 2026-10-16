; V=0x21168  core=0x21168..0x21224（19 条）  过程=0x21168..0x21224（1 块/19 条，段数 1）
; native=[12]
; 内嵌串 core=-
; 库内 CALL -> -
00021168  FRAME_ALLOC   0x4[-]                                   ★ V 入口
00021170  LEA_STK       0x0[-] 0x185F9BC[L_211EC]                
0002117C  LD_STK        0x10[-] 0x185F95C[L_2118C]               
00021188  PUSH          0x0[-]                                   
00021190  PUSH          0x1[-]                                   
00021198  MOV_D         0x183B048[var#810] 0x185F978[L_211A8]    
000211A4  PUSH          0x0[-]                                   
000211AC  MOV_D         0x183B148[var#812] 0x185F98C[L_211BC]    
000211B8  PUSH          0x0[-]                                   
000211C0  PUSH          0x0[-]                                   
000211C8  PUSH          0x1[-]                                   
000211D0  LD_STK        0x24[-] 0x185F9B0[L_211E0]               
000211DC  PUSH          0x0[-]                                   
000211E4  CALLNATIVE    0xD[native#12] 0x0[-] 0x185F9D0[L_21200] 
000211F4  SP_DROP       0x1C[-]                                  
000211FC  ST_STK        0x0[-] 0x4[-]                            
00021208  LD_STK        0x4[-] 0x185F9F0[L_21220]                
00021214  SP_DROP       0x4[-]                                   
0002121C  RETVAL_RET    0x0[-]                                   
