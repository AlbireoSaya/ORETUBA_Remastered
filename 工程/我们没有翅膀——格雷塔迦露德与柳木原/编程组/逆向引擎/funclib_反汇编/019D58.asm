; V=0x19D58  core=0x19D58..0x19D84（5 条）  过程=0x19D58..0x19DCC（5 块/12 条，段数 1）
; native=-
; 内嵌串 core=-
; 库内 CALL -> -
00019D58  FRAME_ALLOC   0x8[-]                                   ★ V 入口
00019D60  MOV_D         0x183E1B8[var#905] 0x1858540[L_19D70]    
00019D6C  JZ            0x0[-] 0x1858554[L_19D84]                
00019D78  SP_DROP       0x8[-]                                   
00019D80  RET                                                    
00019D84  LD_STK        0x10[-] 0x1858564[L_19D94]               
00019D90  JZ            0x0[-] 0x1858580[L_19DB0]                
00019D9C  ST_STK        0x3[-] 0x8[-]                            
00019DA8  JMP           0x185858C[L_19DBC]                       
00019DB0  ST_STK        0x2[-] 0x8[-]                            
00019DBC  ST_STK        0x0[-] 0x4[-]                            
00019DC8  HALT_OK                                                
