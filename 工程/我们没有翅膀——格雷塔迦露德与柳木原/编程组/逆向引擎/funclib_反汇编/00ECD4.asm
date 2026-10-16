; V=0xECD4  core=0xECD4..0xECF4（3 条）  过程=0xECD4..0xED64（2 块/16 条，段数 1）
; native=-
; 内嵌串 core=-
; 库内 CALL -> ['0x98e0', '0x1d4bc']
0000ECD4  MOV_D         0x183E1B8[var#905] 0x184D4B4[L_ECE4]     ★ V 入口
0000ECE0  JZ            0x0[-] 0x184D4C4[L_ECF4]                 
0000ECEC  RETVAL_RET    0x0[-]                                   
0000ECF4  LD_STK        0x8[-] 0x184D4D4[L_ED04]                 
0000ED00  PUSH          0x0[-]                                   
0000ED08  CALL          0x18480B0[L_98E0]                        
0000ED10  SP_DROP       0x4[-]                                   
0000ED18  STORE_RETVAL  0x1869F06[str@""]                        
0000ED20  LD_STK        0xC[-] 0x184D500[L_ED30]                 
0000ED2C  PUSH          0x0[-]                                   
0000ED34  LD_STK        0xC[-] 0x184D514[L_ED44]                 
0000ED40  PUSH          0x0[-]                                   
0000ED48  CALL          0x185BC8C[L_1D4BC]                       
0000ED50  SP_DROP       0x8[-]                                   
0000ED58  STORE_RETVAL  0x1869F06[str@""]                        
0000ED60  RET                                                    
