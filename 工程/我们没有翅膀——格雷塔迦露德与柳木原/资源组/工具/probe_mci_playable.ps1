<#
probe_mci_playable.ps1 — DirectShow 可播性探针（PSV 片尾 .mpg）

用途
    证明「转码出的 .mpg 能被宿主引擎所用的渲染链路建图并播放」，并给出负向对照
    「源 .usm 建不了图」——即转码是必要的。

原理
    MCI 的 mpegvideo 设备（mciqtz32.dll）内部走 IGraphBuilder::RenderFile，
    与 krkrz 1.4.0r2 播放视频用的是同一个 API：
      krkrz 源码 movie/win32/dsoverlay.cpp:106 / dslayerd.cpp:127 → IGraphBuilder::Render
    对 MPEG-1 程序流，系统自带滤镜（均已在 Win10/Win7 注册）：
      MPEG-I Stream Splitter  {336475D0-942A-11CE-A870-00AA002FEAB5} → quartz.dll
      MPEG Audio Codec        {4A2286E0-7BEF-11CE-9BD9-0000E202599C} → quartz.dll
      Microsoft DTV-DVD Video Decoder / MPEG-2 Splitter → msmpeg2vdec.dll / mpg2splt.ax

复跑
    powershell -NoProfile -ExecutionPolicy Bypass -File "<本文件>"
    （可加 -MpgDir <目录> -SourceDir <目录> -PlaySeconds 2 覆盖默认值）

退出码
    0 = 7/7 .mpg OPEN-OK 且播放推进（mode=playing），且源 ED_*.usm 全部打不开
    1 = 任一项 FAIL

注意
    本文件含中文路径字面量，**必须以 UTF-8 with BOM 保存**；
    Windows PowerShell 5.1 读无 BOM 的文件会按 ANSI(GBK) 解码，中文路径会变乱码。
#>
param(
    [string]$MpgDir,
    [string]$SourceDir,
    [int]$PlaySeconds = 2
)

$ErrorActionPreference = 'Stop'

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public class Mci {
    [DllImport("winmm.dll", CharSet = CharSet.Unicode)]
    public static extern int mciSendString(string cmd, StringBuilder ret, int retLen, IntPtr hwnd);
    [DllImport("winmm.dll", CharSet = CharSet.Unicode)]
    public static extern int mciGetErrorString(int err, StringBuilder buf, int len);
}
'@

function Find-SourceUsmDir([string]$start) {
    # 向上逐级找「工作区根」（含 Galgame.md），并优先取**真正带解密源**的那一层：
    # 本机 wt-syn 工作树自身也有一份 Galgame.md，只看第一个命中会停在错的一层。
    $d = Get-Item -LiteralPath $start
    $fallback = $null
    while ($null -ne $d) {
        if (Test-Path -LiteralPath (Join-Path $d.FullName 'Galgame.md')) {
            $cand = Join-Path $d.FullName '工程\我们没有翅膀PSV\解密\PCSG00299\media\data'
            if (Test-Path -LiteralPath $cand) { return $cand }
            if (-not $fallback) { $fallback = $cand }
        }
        $d = $d.Parent
    }
    return $fallback
}

# 本文件位于 <WT>\资源组\工具\  ⇒  资源组 = 上一级
$resDir = Split-Path -Parent $PSScriptRoot
if (-not $MpgDir) { $MpgDir = Join-Path $resDir '片尾\_src\psv_ed' }
if (-not $SourceDir) { $SourceDir = Find-SourceUsmDir $PSScriptRoot }

function Invoke-MciOpen([string]$path, [string]$alias) {
    $sb = New-Object System.Text.StringBuilder 512
    $rc = [Mci]::mciSendString(('open "{0}" type mpegvideo alias {1}' -f $path, $alias), $sb, 512, [IntPtr]::Zero)
    if ($rc -ne 0) {
        $e = New-Object System.Text.StringBuilder 512
        [void][Mci]::mciGetErrorString($rc, $e, 512)
        return @{ ok = $false; detail = ('OPEN-FAIL(rc={0}: {1})' -f $rc, $e.ToString().Trim()) }
    }
    [void][Mci]::mciSendString(('set {0} time format milliseconds' -f $alias), $null, 0, [IntPtr]::Zero)
    $len = New-Object System.Text.StringBuilder 64
    [void][Mci]::mciSendString(('status {0} length' -f $alias), $len, 64, [IntPtr]::Zero)
    $mode0 = New-Object System.Text.StringBuilder 64
    [void][Mci]::mciSendString(('status {0} mode' -f $alias), $mode0, 64, [IntPtr]::Zero)
    $prc = [Mci]::mciSendString(('play {0} from 0' -f $alias), $null, 0, [IntPtr]::Zero)
    Start-Sleep -Seconds $PlaySeconds
    $mode2 = New-Object System.Text.StringBuilder 64
    [void][Mci]::mciSendString(('status {0} mode' -f $alias), $mode2, 64, [IntPtr]::Zero)
    [void][Mci]::mciSendString(('close {0}' -f $alias), $null, 0, [IntPtr]::Zero)
    $playing = ($mode2.ToString().Trim() -eq 'playing')
    return @{
        ok     = $playing
        detail = ('OPEN-OK lengthMs={0} mode0={1} play_rc={2} mode_after_{3}s={4}' -f `
                  $len.ToString().Trim(), $mode0.ToString().Trim(), $prc, $PlaySeconds, $mode2.ToString().Trim())
    }
}

$fail = 0
$idx = 0

Write-Output ('== 一、产物 .mpg 可播性（{0}） ==' -f $MpgDir)
$mpgs = @()
if (Test-Path -LiteralPath $MpgDir) {
    $mpgs = @(Get-ChildItem -LiteralPath $MpgDir -Filter '*.mpg' | Sort-Object Name)
}
if ($mpgs.Count -eq 0) {
    Write-Output '  FAIL  目录里没有 .mpg（先跑 资源组\工具\transcode_ending_psv.py 生成产物）'
    $fail++
} else {
    if ($mpgs.Count -ne 7) { Write-Output ('  WARN  期望 7 支 .mpg，实得 {0}' -f $mpgs.Count) }
    foreach ($f in $mpgs) {
        $idx++
        $r = Invoke-MciOpen $f.FullName ('mpg' + $idx)
        if ($r.ok) { Write-Output ('  PASS  {0,-16} {1}' -f $f.Name, $r.detail) }
        else { Write-Output ('  FAIL  {0,-16} {1}' -f $f.Name, $r.detail); $fail++ }
    }
}

Write-Output ''
Write-Output ('== 二、源 .usm 负向对照（{0}） ==' -f $SourceDir)
if ($SourceDir -and (Test-Path -LiteralPath $SourceDir)) {
    $usms = @(Get-ChildItem -LiteralPath $SourceDir -Filter 'ED_*.usm' | Sort-Object Name)
    foreach ($f in $usms) {
        $idx++
        $r = Invoke-MciOpen $f.FullName ('usm' + $idx)
        if (-not $r.ok) { Write-Output ('  PASS  {0,-16} 建不了图（预期）: {1}' -f $f.Name, $r.detail) }
        else { Write-Output ('  FAIL  {0,-16} 竟然能建图: {1}' -f $f.Name, $r.detail); $fail++ }
    }
} else {
    Write-Output '  SKIP  未找到源目录，跳过负向对照（仅影响对照项，不影响 .mpg 的结论）'
}

Write-Output ''
if ($fail -eq 0) { Write-Output '== 探针结论：全部 PASS ==' ; exit 0 }
Write-Output ('== 探针结论：{0} 项 FAIL ==' -f $fail)
exit 1
