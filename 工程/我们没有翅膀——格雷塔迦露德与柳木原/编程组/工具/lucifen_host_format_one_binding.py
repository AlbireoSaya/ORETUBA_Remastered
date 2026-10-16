"""导入装载系统 user32。这是 caller 限定恰好一个 %s 的 cdecl 三参数 raw 绑定。caller 负责格式/容量/指针及缓冲生命期验证,本模块不作检查。"""
import ctypes
user32=ctypes.CDLL('user32.dll')
wsprintfA_one_string=user32.wsprintfA
wsprintfA_one_string.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
wsprintfA_one_string.restype=ctypes.c_int