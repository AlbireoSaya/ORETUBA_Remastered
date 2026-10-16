; V=0x19A68  core=0x19A68..0x19A98（5 条）  过程=0x19A68..0x19B40（6 块/23 条，段数 1）
; native=-
; 内嵌串 core=-
; 库内 CALL -> ['0x14084']
00019A68  FRAME_ALLOC   0x4[-]                                   ★ V 入口
00019A70  MOV_D         0x183E1B8[var#905] 0x1858250[L_19A80]    
00019A7C  JZ            0x0[-] 0x1858268[L_19A98]                
00019A88  SP_DROP       0x4[-]                                   
00019A90  RETVAL_RET    0x0[-]                                   
00019A98  ST_STK        0x0[-] 0x4[-]                            
00019AA4  LD_STK        0x4[-] 0x1858284[L_19AB4]                
00019AB0  LT            0x0[-] 0x6[-] 0x1858294[L_19AC4]         
00019AC0  JZ            0x0[-] 0x1858304[L_19B34]                
00019ACC  JMP           0x18582B4[L_19AE4]                       
00019AD4  INC_S         0x4[-]                                   
00019ADC  JMP           0x1858274[L_19AA4]                       
00019AE4  LD_STK        0x4[-] 0x18582C4[L_19AF4]                
00019AF0  PUSH          0x0[-]                                   
00019AF8  PUSH          0x0[-]                                   
00019B00  LD_STK        0x14[-] 0x18582E0[L_19B10]               
00019B0C  PUSH          0x0[-]                                   
00019B14  CALL          0x1852854[L_14084]                       
00019B1C  SP_DROP       0xC[-]                                   
00019B24  STORE_RETVAL  0x1869F06[str@""]                        
00019B2C  JMP           0x18582A4[L_19AD4]                       
00019B34  SP_DROP       0x4[-]                                   
00019B3C  RET                                                    
