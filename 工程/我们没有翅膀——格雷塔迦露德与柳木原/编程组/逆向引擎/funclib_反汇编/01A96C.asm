; V=0x1A96C  core=0x1A96C..0x1A988（3 条）  过程=0x1A96C..0x1A9E0（2 块/13 条，段数 1）
; native=-
; 内嵌串 core=-
; 库内 CALL -> ['0x1a31c']
0001A96C  MOV_D         0x183E1B8[var#905] 0x185914C[L_1A97C]    ★ V 入口
0001A978  JZ            0x0[-] 0x1859158[L_1A988]                
0001A984  RET                                                    
0001A988  LD_STK        0x10[-] 0x1859168[L_1A998]               
0001A994  PUSH          0x0[-]                                   
0001A99C  LD_STK        0x10[-] 0x185917C[L_1A9AC]               
0001A9A8  PUSH          0x0[-]                                   
0001A9B0  LD_STK        0x10[-] 0x1859190[L_1A9C0]               
0001A9BC  PUSH          0x0[-]                                   
0001A9C4  CALL          0x1858AEC[L_1A31C]                       
0001A9CC  SP_DROP       0xC[-]                                   
0001A9D4  STORE_RETVAL  0x1869F06[str@""]                        
0001A9DC  RET                                                    
