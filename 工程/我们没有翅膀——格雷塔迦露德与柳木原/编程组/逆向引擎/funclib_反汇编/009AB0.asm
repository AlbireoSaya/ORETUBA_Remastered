; V=0x9AB0  core=0x9AB0..0x9ACC（3 条）  过程=0x9AB0..0x9B88（2 块/21 条，段数 1）
; native=[414]
; 内嵌串 core=-
; 库内 CALL -> ['0x98e0']
00009AB0  MOV_D         0x183E1B8[var#905] 0x1848290[L_9AC0]     ★ V 入口
00009ABC  JZ            0x0[-] 0x184829C[L_9ACC]                 
00009AC8  RET                                                    
00009ACC  LD_STK        0x8[-] 0x18482AC[L_9ADC]                 
00009AD8  PUSH          0x0[-]                                   
00009AE0  CALL          0x18480B0[L_98E0]                        
00009AE8  SP_DROP       0x4[-]                                   
00009AF0  STORE_RETVAL  0x1869F06[str@""]                        
00009AF8  LEA_STK       0x0[-] 0x1848344[L_9B74]                 
00009B04  MOV           0x183DD38[var#896] 0x1848300[L_9B30]     
00009B10  LD_STK        0x8[-] 0x18482F0[L_9B20]                 
00009B1C  MUL           0x0[-] 0x4[-] 0x1848304[L_9B34]          
00009B2C  ADD           0x0[-] 0x0[-] 0x1848310[L_9B40]          
00009B3C  MOV_D         0x0[-] 0x184831C[L_9B4C]                 
00009B48  PUSH          0x0[-]                                   
00009B50  LD_STK        0x10[-] 0x1848330[L_9B60]                
00009B5C  PUSH          0x0[-]                                   
00009B64  PUSH          0x2[-]                                   
00009B6C  CALLNATIVE    0x19F[native#414] 0x0[-] 0x1869F06[str@""] 
00009B7C  SP_DROP       0xC[-]                                   
00009B84  RET                                                    
