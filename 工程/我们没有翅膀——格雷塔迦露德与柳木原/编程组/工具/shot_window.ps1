# shot_window.ps1 —— 只抓 tvpwin32 主窗口
# 两级策略：
#   ① `PrintWindow(hwnd, hdc, PW_RENDERFULLCONTENT=2)` —— Win8.1+ 可抓 DirectComposition/D3D 内容
#   ② 失败则退回 GDI `CopyFromScreen`
# ⚠️ 本工程已知：**D3D 窗口 GDI 抓屏读不到内容**（历史上全黑、本轮全白）⇒ ① 才是主路径。
# 用法: powershell -NoProfile -ExecutionPolicy Bypass -File shot_window.ps1 <输出png绝对路径>
param([string]$Out)
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
$p = Get-Process tvpwin32 -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Output "NO_WINDOW"; exit 2 }
$r = New-Object W+RECT
[void][W]::GetWindowRect($p.MainWindowHandle, [ref]$r)
$w = $r.R - $r.L; $h = $r.B - $r.T
if ($w -le 0 -or $h -le 0) { Write-Output "BAD_RECT $w x $h"; exit 3 }
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$ok = $false
try {
  $hdc = $g.GetHdc()
  # PW_RENDERFULLCONTENT = 2
  $ok = [W]::PrintWindow($p.MainWindowHandle, $hdc, 2)
  $g.ReleaseHdc($hdc)
} catch { $ok = $false }
if (-not $ok) {
  try {
    $g.CopyFromScreen($r.L, $r.T, 0, 0, (New-Object System.Drawing.Size $w, $h))
    $ok = "gdi"
  } catch { $ok = $false }
}
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output ("PRINTWINDOW=" + $ok + " size=" + $w + "x" + $h + " -> " + $Out)
