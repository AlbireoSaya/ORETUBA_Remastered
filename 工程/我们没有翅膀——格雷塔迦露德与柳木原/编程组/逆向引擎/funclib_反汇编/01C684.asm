; V=0x1C684  core=0x1C684..0x1C6A0（3 条）  过程=0x1C684..0x1C738（5 块/17 条，段数 2）
; native=[537, 538]
; 内嵌串 core=-
; 库内 CALL -> -
0001C684  MOV_D         0x183E1B8[var#905] 0x185AE64[L_1C694]    ★ V 入口
0001C690  JZ            0x0[-] 0x185AE70[L_1C6A0]                
0001C69C  RET                                                    
0001C6A0  LEA_STK       0x0[-] 0x185AE8C[L_1C6BC]                
0001C6AC  PUSH          0x0[-]                                   
0001C6B4  CALLNATIVE    0x21A[native#537] 0x0[-] 0x1869F06[str@""] 
0001C6C4  SP_DROP       0x4[-]                                   
0001C6CC  LEA_STK       0x0[-] 0x185AEB8[L_1C6E8]                
0001C6D8  PUSH          0x0[-]                                   
0001C6E0  CALLNATIVE    0x21B[native#538] 0x0[-] 0x185AED8[L_1C708] 
0001C6F0  SP_DROP       0x4[-]                                   
0001C6F8  LD_STK        0x8[-] 0x185AEDC[L_1C70C]                
0001C704  GT            0x0[-] 0x0[-] 0x185AEE8[L_1C718]         
0001C714  JZ            0x0[-] 0x185AEF8[L_1C728]                
0001C720  JMP           0x185AF04[L_1C734]                       
0001C728  HALT_OK                                                
0001C734  RET                                                    
