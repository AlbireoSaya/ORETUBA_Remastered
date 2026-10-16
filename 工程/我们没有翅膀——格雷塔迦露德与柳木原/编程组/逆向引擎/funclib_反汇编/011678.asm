; V=0x11678  core=0x11678..0x116A4（5 条）  过程=0x11678..0x11784（2 块/25 条，段数 1）
; native=-
; 内嵌串 core=-
; 库内 CALL -> ['0xeb50']
00011678  FRAME_ALLOC   0x4[-]                                   ★ V 入口
00011680  MOV_D         0x183E1B8[var#905] 0x184FE60[L_11690]    
0001168C  JZ            0x0[-] 0x184FE74[L_116A4]                
00011698  SP_DROP       0x4[-]                                   
000116A0  RET                                                    
000116A4  MOV           0x183B588[var#820] 0x184FEA0[L_116D0]    
000116B0  LD_STK        0xC[-] 0x184FE90[L_116C0]                
000116BC  MUL           0x0[-] 0x4[-] 0x184FEA4[L_116D4]         
000116CC  ADD           0x0[-] 0x0[-] 0x184FEB0[L_116E0]         
000116DC  MOV_D         0x0[-] 0x184FEBC[L_116EC]                
000116E8  ST_STK        0x0[-] 0x4[-]                            
000116F4  LD_STK        0x4[-] 0x184FED4[L_11704]                
00011700  PUSH          0x0[-]                                   
00011708  LD_STK        0x14[-] 0x184FEE8[L_11718]               
00011714  PUSH          0x0[-]                                   
0001171C  CALL          0x184D320[L_EB50]                        
00011724  SP_DROP       0x8[-]                                   
0001172C  STORE_RETVAL  0x1869F06[str@""]                        
00011734  MOV           0x183B588[var#820] 0x184FF30[L_11760]    
00011740  LD_STK        0xC[-] 0x184FF20[L_11750]                
0001174C  MUL           0x0[-] 0x4[-] 0x184FF34[L_11764]         
0001175C  ADD           0x0[-] 0x0[-] 0x184FF44[L_11774]         
0001176C  MOV           0x0[-] 0x0[-]                            
00011778  SP_DROP       0x4[-]                                   
00011780  RET                                                    
