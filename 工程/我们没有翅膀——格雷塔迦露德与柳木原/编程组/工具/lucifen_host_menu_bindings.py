"""lucifen_host_menu_bindings.py

user32 菜单相关 Win32 API 的原始绑定声明。

约定（由调用方遵守，本模块不作任何验证或策略）：
  * 调用方只操作自有窗口的菜单。
  * fullhost 指针全程以 c_void_p 承载，不得截断为 32 位。
  * GetMenu / GetSystemMenu 返回的是 borrowed（借用）菜单句柄，
    不得对其调用 DestroyMenu。
  * 真实 NULL、真实的 BOOL -1（32 位位形 0xFFFFFFFF）、以及 LastError
    均由调用方自行保留与判读；本模块不捏造成功结果。
  * use_last_error=True，调用方可经 ctypes.get_last_error() 读取上次错误码。
"""

import ctypes

# user32 仅加载一次。
_user32 = ctypes.WinDLL("user32", use_last_error=True)

# HMENU GetMenu(HWND hWnd);
GetMenu = _user32.GetMenu
GetMenu.restype = ctypes.c_void_p
GetMenu.argtypes = [ctypes.c_void_p]

# HMENU GetSystemMenu(HWND hWnd, BOOL bRevert);
GetSystemMenu = _user32.GetSystemMenu
GetSystemMenu.restype = ctypes.c_void_p
GetSystemMenu.argtypes = [ctypes.c_void_p, ctypes.c_int]

# BOOL DeleteMenu(HMENU hMenu, UINT uPosition, UINT uFlags);
DeleteMenu = _user32.DeleteMenu
DeleteMenu.restype = ctypes.c_int
DeleteMenu.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]

# BOOL EnableMenuItem(HMENU hMenu, UINT uIDEnableItem, UINT uEnable);
EnableMenuItem = _user32.EnableMenuItem
EnableMenuItem.restype = ctypes.c_int
EnableMenuItem.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]

# BOOL DrawMenuBar(HWND hWnd);
DrawMenuBar = _user32.DrawMenuBar
DrawMenuBar.restype = ctypes.c_int
DrawMenuBar.argtypes = [ctypes.c_void_p]
