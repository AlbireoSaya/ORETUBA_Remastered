; V=0x1C330  core=0x1C330..0x1C35C（5 条）  过程=0x1C330..0x1C3C0（2 块/16 条，段数 1）
; native=-
; 内嵌串 core=-
; 库内 CALL -> ['0xeb50']
0001C330  FRAME_ALLOC   0x4[-]                                   ★ V 入口
0001C338  MOV_D         0x183E1B8[var#905] 0x185AB18[L_1C348]    
0001C344  JZ            0x0[-] 0x185AB2C[L_1C35C]                
0001C350  SP_DROP       0x4[-]                                   
0001C358  RET                                                    
0001C35C  ST_STK_D      0x183BE48[var#836] 0x4[-]                
0001C368  LD_STK        0x4[-] 0x185AB48[L_1C378]                
0001C374  PUSH          0x0[-]                                   
0001C37C  LD_STK        0x10[-] 0x185AB5C[L_1C38C]               
0001C388  PUSH          0x0[-]                                   
0001C390  CALL          0x184D320[L_EB50]                        
0001C398  SP_DROP       0x8[-]                                   
0001C3A0  STORE_RETVAL  0x1869F06[str@""]                        
0001C3A8  MOV           0x0[-] 0x183BE48[var#836]                
0001C3B4  SP_DROP       0x4[-]                                   
0001C3BC  RET                                                    
