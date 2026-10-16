using System;
using System.Runtime.InteropServices;
using System.Text;
using System.IO;
using System.ComponentModel;

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
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFO
    {
        public uint cb;
        public IntPtr lpReserved;
        public string lpDesktop;
        public string lpTitle;
        public uint dwX;
        public uint dwY;
        public uint dwXSize;
        public uint dwYSize;
        public uint dwXCountChars;
        public uint dwYCountChars;
        public uint dwFillAttribute;
        public uint dwFlags;
        public ushort wShowWindow;
        public ushort cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public uint dwProcessId;
        public uint dwThreadId;
    }

    [DllImport("advapi32.dll", EntryPoint = "CreateProcessAsUserW", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool CreateProcessAsUserW(
        IntPtr hToken,
        string lpApplicationName,
        StringBuilder lpCommandLine,
        IntPtr lpProcessAttributes,
        IntPtr lpThreadAttributes,
        bool bInheritHandles,
        uint dwCreationFlags,
        IntPtr lpEnvironment,
        string lpCurrentDirectory,
        ref STARTUPINFO lpStartupInfo,
        out PROCESS_INFORMATION lpProcessInformation);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool GetExitCodeProcess(IntPtr hProcess, out uint lpExitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool TerminateProcess(IntPtr hProcess, uint uExitCode);
}

public static partial class RestrictedWriteProbe
{
	public static IntPtr MakePrimaryToken(string sidText)
	{
		IntPtr source = IntPtr.Zero;
		IntPtr sid = IntPtr.Zero;
		IntPtr restricted = IntPtr.Zero;
		try
		{
			if (!OpenProcessToken(GetCurrentProcess(), 15, out source))
				throw new Win32Exception(Marshal.GetLastWin32Error());
			if (!ConvertStringSidToSidW(sidText, out sid))
				throw new Win32Exception(Marshal.GetLastWin32Error());
			SID_AND_ATTRIBUTES[] restrictedSids = new SID_AND_ATTRIBUTES[1];
			restrictedSids[0].Sid = sid;
			restrictedSids[0].Attributes = 0;
			if (!CreateRestrictedToken(source, 9, 0, IntPtr.Zero, 0, IntPtr.Zero, 1, restrictedSids, out restricted))
				throw new Win32Exception(Marshal.GetLastWin32Error());
if (!IsTokenRestricted(restricted))
    throw new System.InvalidOperationException("Token is restricted.");
			IntPtr result = restricted;
			restricted = IntPtr.Zero;
			return result;
		}
		catch
		{
			if (restricted != IntPtr.Zero)
			{
				CloseHandle(restricted);
				restricted = IntPtr.Zero;
			}
			throw;
		}
		finally
		{
			if (source != IntPtr.Zero)
				CloseHandle(source);
			if (sid != IntPtr.Zero)
				LocalFree(sid);
		}
	}

	public static int Main(string[] a)
	{
		try
		{
			if (a == null || a.Length < 3)
			{
				Console.Error.WriteLine("ERROR Argument");
				return 1;
			}
			string output = Path.GetFullPath(a[0]);
			string root = "E:\\ZCode Workspace\\Galgame\\";
			if (!output.StartsWith(root, StringComparison.Ordinal))
			{
				Console.Error.WriteLine("ERROR OutputOutsideRoot " + output);
				return 1;
			}
			if (!Directory.Exists(output))
			{
				Console.Error.WriteLine("ERROR OutputMissing " + output);
				return 1;
			}
			if (File.Exists(Path.Combine(output, "probe-canary.bin")) || File.Exists(Path.Combine(output, "child-report.log")))
			{
				Console.Error.WriteLine("ERROR PreExistingArtifact " + output);
				return 1;
			}
			string[] negatives = new string[a.Length - 2];
			Array.Copy(a, 2, negatives, 0, negatives.Length);
			int i;
			for (i = 0; i < negatives.Length; i++)
			{
				negatives[i] = Path.GetFullPath(negatives[i]);
				if (!File.Exists(negatives[i]))
				{
					Console.Error.WriteLine("ERROR NegativeMissing " + negatives[i]);
					return 1;
				}
			}
			IntPtr token = MakePrimaryToken(a[1]);
			try
			{
				return LaunchFixedProbe(token, output, negatives);
			}
			finally
			{
				CloseHandle(token);
			}
		}
		catch (Exception ex)
		{
			Win32Exception w = ex as Win32Exception;
			if (w != null)
				Console.Error.WriteLine("ERROR " + ex.GetType().Name + " " + w.NativeErrorCode);
			else
				Console.Error.WriteLine("ERROR " + ex.GetType().Name);
			return 1;
		}
	}
}

public static partial class RestrictedWriteProbe
{
    public static int LaunchFixedProbe(IntPtr token, string outDir, string[] negatives)
    {
        string childExe = Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location), "RestrictedFileChild.exe");
        if (!File.Exists(childExe)) throw new FileNotFoundException("RestrictedFileChild.exe not found", childExe);
        string[] all = new string[negatives.Length + 2];
        all[0] = childExe;
        all[1] = outDir;
        Array.Copy(negatives, 0, all, 2, negatives.Length);
        StringBuilder cmd = new StringBuilder();
        for (int i = 0; i < all.Length; i++)
        {
            string a = all[i];
            if (a == null || a.IndexOf('"') >= 0 || a.IndexOf('\0') >= 0 || a.EndsWith("\\", StringComparison.Ordinal))
                throw new ArgumentException("invalid arg: " + a);
            if (cmd.Length > 0) cmd.Append(' ');
            cmd.Append('"').Append(a).Append('"');
        }
        STARTUPINFO si = new STARTUPINFO();
        si.cb = (uint)Marshal.SizeOf(typeof(STARTUPINFO));
        si.lpDesktop = null;
        PROCESS_INFORMATION pi;
        if (!CreateProcessAsUserW(token, childExe, cmd, IntPtr.Zero, IntPtr.Zero, false, 0x00000008, IntPtr.Zero, outDir, ref si, out pi))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        Console.WriteLine("CREATE_PROCESS pid=" + pi.dwProcessId);
        bool done = false;
        try
        {
            uint wait = WaitForSingleObject(pi.hProcess, 15000);
            if (wait != 0) throw new InvalidOperationException("wait=" + wait);
            done = true;
            uint exit;
            if (!GetExitCodeProcess(pi.hProcess, out exit)) throw new Win32Exception(Marshal.GetLastWin32Error());
            Console.WriteLine("CHILD_EXIT " + exit);
            return exit == 0 ? 0 : 1;
        }
        finally
        {
            if (!done)
            {
                if (!TerminateProcess(pi.hProcess, 1) || WaitForSingleObject(pi.hProcess, 5000) != 0)
                    Console.WriteLine("CLEANUP_FAILED");
            }
            if (pi.hThread != IntPtr.Zero) CloseHandle(pi.hThread);
            if (pi.hProcess != IntPtr.Zero) CloseHandle(pi.hProcess);
        }
    }
}
