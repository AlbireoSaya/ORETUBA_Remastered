; V=0x19B40  core=0x19B40..0x19BA4（10 条）  过程=0x19B40..0x19BA8（2 块/11 条，段数 1）
; native=-
; 内嵌串 core=['']
; 库内 CALL -> ['0x28018', '0x2928c']
00019B40  MOV           0x1[-] 0x183BAC8[var#829]                ★ V 入口
00019B4C  PUSH          0x1[-]                                   
00019B54  CALL          0x18667E8[L_28018]                       
00019B5C  SP_DROP       0x4[-]                                   
00019B64  STORE_RETVAL  0x1869F06[str@""]                        
00019B6C  MOV_D         0x183BB48[var#830] 0x185834C[L_19B7C]    
00019B78  EQ            0x0[-] 0x1[-] 0x185835C[L_19B8C]         
00019B88  JZ            0x0[-] 0x1858374[L_19BA4]                
00019B94  CALL          0x1867A5C[L_2928C]                       
00019B9C  STORE_RETVAL  0x1869F06[str@""]                        
00019BA4  RET                                                    
