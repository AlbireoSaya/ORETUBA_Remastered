; V=0x1C5B0  core=0x1C5B0..0x1C5CC（3 条）  过程=0x1C5B0..0x1C684（3 块/23 条，段数 1）
; native=-
; 内嵌串 core=-
; 库内 CALL -> ['0x83fc', '0x19a68', '0x1a31c']
0001C5B0  MOV_D         0x183E1B8[var#905] 0x185AD90[L_1C5C0]    ★ V 入口
0001C5BC  JZ            0x0[-] 0x185AD9C[L_1C5CC]                
0001C5C8  RET                                                    
0001C5CC  CALL          0x1846BCC[L_83FC]                        
0001C5D4  STORE_RETVAL  0x1869F06[str@""]                        
0001C5DC  PUSH          0x1[-]                                   
0001C5E4  CALL          0x1858238[L_19A68]                       
0001C5EC  SP_DROP       0x4[-]                                   
0001C5F4  STORE_RETVAL  0x1869F06[str@""]                        
0001C5FC  LD_STK        0x10[-] 0x185ADDC[L_1C60C]               
0001C608  EQZ           0x0[-] 0x185ADE8[L_1C618]                
0001C614  JZ            0x0[-] 0x185ADFC[L_1C62C]                
0001C620  ST_STK        0x12C[-] 0x10[-]                         
0001C62C  LD_STK        0x10[-] 0x185AE0C[L_1C63C]               
0001C638  PUSH          0x0[-]                                   
0001C640  LD_STK        0x10[-] 0x185AE20[L_1C650]               
0001C64C  PUSH          0x0[-]                                   
0001C654  LD_STK        0x10[-] 0x185AE34[L_1C664]               
0001C660  PUSH          0x0[-]                                   
0001C668  CALL          0x1858AEC[L_1A31C]                       
0001C670  SP_DROP       0xC[-]                                   
0001C678  STORE_RETVAL  0x1869F06[str@""]                        
0001C680  RET                                                    
