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
    public static void WithRestrictedToken(string sidText, Action body)
    {
        IntPtr token = IntPtr.Zero, sid = IntPtr.Zero, restricted = IntPtr.Zero;
        bool impersonating = false;
        try
        {
            if (!OpenProcessToken(GetCurrentProcess(), 14, out token))
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            if (!ConvertStringSidToSidW(sidText, out sid))
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            if (!CreateRestrictedToken(token, 9, 0, IntPtr.Zero, 0, IntPtr.Zero, 1, new[] { new SID_AND_ATTRIBUTES { Sid = sid, Attributes = 0 } }, out restricted))
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            if (!IsTokenRestricted(restricted))
                throw new InvalidOperationException("Token is not restricted.");
            if (!ImpersonateLoggedOnUser(restricted))
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            impersonating = true;
            body();
        }
        finally
        {
            if (impersonating && !RevertToSelf())
                Environment.FailFast("RevertToSelf failed.");
            if (restricted != IntPtr.Zero && !CloseHandle(restricted))
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            if (token != IntPtr.Zero && !CloseHandle(token))
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            if (sid != IntPtr.Zero && LocalFree(sid) != IntPtr.Zero)
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        }
    }
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

public static partial class RestrictedWriteProbe {
    public static int Main(string[] a) {
        try {
            if (a.Length < 3) { Console.WriteLine("FAIL"); return 1; }
            string outDir = Path.GetFullPath(a[0]);
            if (!outDir.StartsWith("E:\\ZCode Workspace\\Galgame\\", StringComparison.OrdinalIgnoreCase) || !Directory.Exists(outDir)) { Console.WriteLine("FAIL"); return 1; }
            if (File.Exists(Path.Combine(outDir, "probe-canary.bin"))) { Console.WriteLine("FAIL"); return 1; }
            string[] negatives = new string[a.Length - 2];
            Array.Copy(a, 2, negatives, 0, negatives.Length);
            bool baseline = false;
            foreach (string p in negatives) {
                if (!File.Exists(p)) { Console.WriteLine("FAIL"); return 1; }
                int error;
                bool ok = CheckOpen(p, 0x40000000, out error);
                Console.WriteLine("BASE " + p + " " + (ok ? "granted" : "denied") + "," + error);
                if (ok) baseline = true;
            }
            int result = 1;
            WithRestrictedToken(a[1], delegate { result = CheckFiles(outDir, negatives); });
            bool pass = baseline && result == 0;
            Console.WriteLine(pass ? "PASS" : "FAIL");
            return pass ? 0 : 1;
        } catch (Exception ex) {
            System.ComponentModel.Win32Exception w = ex as System.ComponentModel.Win32Exception;
            Console.WriteLine("FAIL " + ex.GetType().FullName + " " + (w != null ? w.NativeErrorCode : 0));
            return 1;
        }
    }
}
