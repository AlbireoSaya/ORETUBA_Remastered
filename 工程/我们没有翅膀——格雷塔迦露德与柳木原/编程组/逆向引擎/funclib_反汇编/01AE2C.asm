; V=0x1AE2C  core=0x1AE2C..0x1AE48（3 条）  过程=0x1AE2C..0x1AEA0（2 块/13 条，段数 1）
; native=-
; 内嵌串 core=-
; 库内 CALL -> ['0x1a9e0']
0001AE2C  MOV_D         0x183E1B8[var#905] 0x185960C[L_1AE3C]    ★ V 入口
0001AE38  JZ            0x0[-] 0x1859618[L_1AE48]                
0001AE44  RET                                                    
0001AE48  LD_STK        0x10[-] 0x1859628[L_1AE58]               
0001AE54  PUSH          0x0[-]                                   
0001AE5C  LD_STK        0x10[-] 0x185963C[L_1AE6C]               
0001AE68  PUSH          0x0[-]                                   
0001AE70  LD_STK        0x10[-] 0x1859650[L_1AE80]               
0001AE7C  PUSH          0x0[-]                                   
0001AE84  CALL          0x18591B0[L_1A9E0]                       
0001AE8C  SP_DROP       0xC[-]                                   
0001AE94  STORE_RETVAL  0x1869F06[str@""]                        
0001AE9C  RET                                                    
