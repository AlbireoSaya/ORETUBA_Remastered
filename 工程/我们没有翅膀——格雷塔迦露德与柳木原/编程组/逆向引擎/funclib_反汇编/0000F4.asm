; V=0xF4  core=0xF4..0x148（9 条）  过程=0xF4..0x150（2 块/10 条，段数 1）
; native=-
; 内嵌串 core=['']
; 库内 CALL -> ['0x22fdc']
000000F4  MOV_D         0x183E7B8[var#915] 0x183E8D4[L_104]      ★ V 入口
00000100  JZ            0x0[-] 0x183E918[L_148]                  
0000010C  PUSH          0x5[-]                                   
00000114  PUSH          0x1[-]                                   
0000011C  CALL          0x18617AC[L_22FDC]                       
00000124  SP_DROP       0x8[-]                                   
0000012C  STORE_RETVAL  0x1869F06[str@""]                        
00000134  MOV           0x0[-] 0x183E7B8[var#915]                
00000140  RETVAL_RET    0x1[-]                                   
00000148  RETVAL_RET    0x0[-]                                   
