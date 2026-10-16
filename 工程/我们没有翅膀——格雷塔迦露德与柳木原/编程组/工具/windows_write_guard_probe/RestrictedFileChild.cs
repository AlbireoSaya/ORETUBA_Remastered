using System;
using System.Runtime.InteropServices;
using System.IO;

public static partial class RestrictedWriteProbe
{
    [StructLayout(LayoutKind.Sequential)]
    public struct SID_AND_ATTRIBUTES
    {
        public IntPtr Sid;
        public uint Attributes;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr GetCurrentProcess();

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr LocalFree(IntPtr hMem);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern IntPtr CreateFileW(
        string lpFileName,
        uint dwDesiredAccess,
        uint dwShareMode,
        IntPtr lpSecurityAttributes,
        uint dwCreationDisposition,
        uint dwFlagsAndAttributes,
        IntPtr hTemplateFile);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool WriteFile(
        IntPtr hFile,
        byte[] lpBuffer,
        uint nNumberOfBytesToWrite,
        out uint lpNumberOfBytesWritten,
        IntPtr lpOverlapped);

    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool OpenProcessToken(
        IntPtr ProcessHandle,
        uint DesiredAccess,
        out IntPtr TokenHandle);

    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool ConvertStringSidToSidW(
        string StringSid,
        out IntPtr Sid);

    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool CreateRestrictedToken(
        IntPtr ExistingTokenHandle,
        uint Flags,
        uint DisableSidCount,
        IntPtr SidsToDisable,
        uint DeletePrivilegeCount,
        IntPtr PrivilegesToDelete,
        uint RestrictedSidCount,
        [In] SID_AND_ATTRIBUTES[] SidsToRestrict,
        out IntPtr NewTokenHandle);

    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool IsTokenRestricted(IntPtr TokenHandle);

    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool ImpersonateLoggedOnUser(IntPtr hToken);

    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool RevertToSelf();
}

public static partial class RestrictedWriteProbe
{
    public static bool CheckOpen(string path, uint access, out int error)
    {
        IntPtr h = CreateFileW(path, access, 7u, IntPtr.Zero, 3u, 128u, IntPtr.Zero);
        if (h == new IntPtr(-1))
        {
            error = Marshal.GetLastWin32Error();
            return false;
        }
        error = 0;
        CloseHandle(h);
        return true;
    }

    public static int CheckFiles(string outputDir, string[] negatives)
    {
        bool pass = true;
        foreach (string neg in negatives)
        {
            int rerr;
            bool read = CheckOpen(neg, 0x80000000u, out rerr);
            Console.WriteLine("READ granted=" + read + ",error=" + rerr);
            int werr;
            bool write = CheckOpen(neg, 0x40000000u, out werr);
            Console.WriteLine("WRITE granted=" + write + ",error=" + werr);
            if (!read || write || werr != 5) pass = false;
        }

        string canary = Path.Combine(outputDir, "probe-canary.bin");
        IntPtr h = CreateFileW(canary, 0x40000000u, 7u, IntPtr.Zero, 1u, 128u, IntPtr.Zero);
        if (h == new IntPtr(-1)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        try
        {
            byte[] buf = new byte[16];
            uint written;
            if (!WriteFile(h, buf, 16u, out written, IntPtr.Zero))
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            if (written == 16) Console.WriteLine("CANARY written");
            else pass = false;
        }
        finally
        {
            CloseHandle(h);
        }

        Console.WriteLine("scope thread-only");
        return pass ? 0 : 1;
    }
}

public static partial class RestrictedWriteProbe
{
    public static int Main(string[] args)
    {
        try
        {
            if (args.Length < 2) return 1;
            string outdir = Path.GetFullPath(args[0]);
            if (!outdir.StartsWith("E:\\ZCode Workspace\\Galgame\\", StringComparison.OrdinalIgnoreCase)) return 1;
            if (!Directory.Exists(outdir)) return 1;
            string[] negative = new string[args.Length - 1];
            Array.Copy(args, 1, negative, 0, negative.Length);
            foreach (string f in negative) if (!File.Exists(f)) return 1;
            IntPtr token;
            if (!OpenProcessToken(GetCurrentProcess(), 8, out token)) return 1;
            try { if (!IsTokenRestricted(token)) return 1; }
            finally { CloseHandle(token); }
            return CheckFiles(outdir, negative);
        }
        catch { return 1; }
    }
}
