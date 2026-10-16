param([string]$TaskTemp, [UInt32]$MemoryLengthBefore = 32)
$ErrorActionPreference = 'Stop'
if ([IntPtr]::Size -ne 4) { throw 'IntPtr.Size must be 4 (32-bit Windows PowerShell required)' }
if ([string]::IsNullOrWhiteSpace($TaskTemp)) { throw 'TaskTemp is required' }
$work = [System.IO.Path]::GetFullPath($TaskTemp)
$roots = @('E:\ZCode Workspace\Galgame\临时\', 'E:\ZCode Workspace\Galgame\子代理工作区\')
$inside = $false
foreach ($r in $roots) {
  if ($work.Length -gt $r.Length -and $work.StartsWith($r, [System.StringComparison]::OrdinalIgnoreCase)) { $inside = $true; break }
}
if (-not $inside) { throw "TaskTemp outside allowed roots: $work" }
if (-not [System.IO.Directory]::Exists($work)) { $null = [System.IO.Directory]::CreateDirectory($work) }
$env:TEMP = $work
$env:TMP = $work

$cs = @'
using System;
using System.Runtime.InteropServices;

[StructLayout(LayoutKind.Sequential, Pack = 4)]
public struct SYSTEM_INFO
{
    public ushort wProcessorArchitecture;
    public ushort wReserved;
    public uint dwPageSize;
    public IntPtr lpMinimumApplicationAddress;
    public IntPtr lpMaximumApplicationAddress;
    public UIntPtr dwActiveProcessorMask;
    public uint dwNumberOfProcessors;
    public uint dwProcessorType;
    public uint dwAllocationGranularity;
    public ushort wProcessorLevel;
    public ushort wProcessorRevision;
}

[StructLayout(LayoutKind.Sequential, Pack = 4)]
public struct MEMORYSTATUS
{
    public uint dwLength;
    public uint dwMemoryLoad;
    public uint dwTotalPhys;
    public uint dwAvailPhys;
    public uint dwTotalPageFile;
    public uint dwAvailPageFile;
    public uint dwTotalVirtual;
    public uint dwAvailVirtual;
}

public static class Native32
{
    [DllImport("kernel32.dll", EntryPoint = "GetSystemInfo")]
    public static extern void GetSystemInfo(ref SYSTEM_INFO lpSystemInfo);

    [DllImport("kernel32.dll", EntryPoint = "GlobalMemoryStatus")]
    public static extern void GlobalMemoryStatus(ref MEMORYSTATUS lpBuffer);
}
'@

Add-Type -TypeDefinition $cs -Language CSharp -ErrorAction Stop | Out-Null

if ([System.Runtime.InteropServices.Marshal]::SizeOf(([System.Activator]::CreateInstance([SYSTEM_INFO]))) -ne 36) { throw 'SYSTEM_INFO layout is not 36 bytes' }
if ([System.Runtime.InteropServices.Marshal]::SizeOf(([System.Activator]::CreateInstance([MEMORYSTATUS]))) -ne 32) { throw 'MEMORYSTATUS layout is not 32 bytes' }

$pSi = [IntPtr]::Zero
$pMs = [IntPtr]::Zero
try {
  $si = [System.Activator]::CreateInstance([SYSTEM_INFO])
  $pSi = [System.Runtime.InteropServices.Marshal]::AllocHGlobal(36)
  [Native32]::GetSystemInfo([ref]$si)
  [System.Runtime.InteropServices.Marshal]::StructureToPtr($si, $pSi, $false)
  $siBytes = New-Object 'byte[]' 36
  [System.Runtime.InteropServices.Marshal]::Copy($pSi, $siBytes, 0, 36)

  $ms = [System.Activator]::CreateInstance([MEMORYSTATUS])
  $ms.dwLength = $MemoryLengthBefore
  $pMs = [System.Runtime.InteropServices.Marshal]::AllocHGlobal(32)
  [Native32]::GlobalMemoryStatus([ref]$ms)
  [System.Runtime.InteropServices.Marshal]::StructureToPtr($ms, $pMs, $false)
  $msBytes = New-Object 'byte[]' 32
  [System.Runtime.InteropServices.Marshal]::Copy($pMs, $msBytes, 0, 32)
}
finally {
  if ($pSi -ne [IntPtr]::Zero) { [System.Runtime.InteropServices.Marshal]::FreeHGlobal($pSi) }
  if ($pMs -ne [IntPtr]::Zero) { [System.Runtime.InteropServices.Marshal]::FreeHGlobal($pMs) }
}

$siHex = -join ($siBytes | ForEach-Object { $_.ToString('x2') })
$msHex = -join ($msBytes | ForEach-Object { $_.ToString('x2') })

[pscustomobject][ordered]@{
  pointer_size = [IntPtr]::Size
  system_info_hex = $siHex
  memory_status_hex = $msHex
  actual_32bit_Windows_API = $true
} | ConvertTo-Json -Compress