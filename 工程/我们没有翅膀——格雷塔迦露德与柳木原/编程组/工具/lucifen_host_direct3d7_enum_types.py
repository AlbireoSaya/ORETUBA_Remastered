"""
SDK d3d.h slot3 and d3dcaps.h lines358-403; caller verify actualGUID16/PRIMCAPS56/DESC236/deviceGUID offset196, fullwidthownedCOMmethodaddress, guardedcopies/borrowedpointerlifetime; no buffer validation/sandbox or callback logic provided. Register only hostPython callback, no guest addresses. Originalguestcallback executed withoutactiveouteremu_start. Actualoriginalreturn1 continues,0 cancels (root separatelySDKverify); preserve failureHRESULTs. Source content no original game data.
"""
from ctypes import Structure, c_uint32, c_uint16, c_uint8, c_float, c_void_p, c_int32, WINFUNCTYPE


class GUID(Structure):
    _fields_ = [
        ("Data1", c_uint32),
        ("Data2", c_uint16),
        ("Data3", c_uint16),
        ("Data4", c_uint8 * 8),
    ]


class D3DPRIMCAPS(Structure):
    _fields_ = [
        ("dwSize", c_uint32),
        ("dwMiscCaps", c_uint32),
        ("dwRasterCaps", c_uint32),
        ("dwZCmpCaps", c_uint32),
        ("dwSrcBlendCaps", c_uint32),
        ("dwDestBlendCaps", c_uint32),
        ("dwAlphaCmpCaps", c_uint32),
        ("dwShadeCaps", c_uint32),
        ("dwTextureCaps", c_uint32),
        ("dwTextureFilterCaps", c_uint32),
        ("dwTextureBlendCaps", c_uint32),
        ("dwTextureAddressCaps", c_uint32),
        ("dwStippleWidth", c_uint32),
        ("dwStippleHeight", c_uint32),
    ]


class D3DDEVICEDESC7(Structure):
    _fields_ = [
        ("dwDevCaps", c_uint32),
        ("dpcLineCaps", D3DPRIMCAPS),
        ("dpcTriCaps", D3DPRIMCAPS),
        ("dwDeviceRenderBitDepth", c_uint32),
        ("dwDeviceZBufferBitDepth", c_uint32),
        ("dwMinTextureWidth", c_uint32),
        ("dwMinTextureHeight", c_uint32),
        ("dwMaxTextureWidth", c_uint32),
        ("dwMaxTextureHeight", c_uint32),
        ("dwMaxTextureRepeat", c_uint32),
        ("dwMaxTextureAspectRatio", c_uint32),
        ("dwMaxAnisotropy", c_uint32),
        ("dvGuardBandLeft", c_float),
        ("dvGuardBandTop", c_float),
        ("dvGuardBandRight", c_float),
        ("dvGuardBandBottom", c_float),
        ("dvExtentsAdjust", c_float),
        ("dwStencilCaps", c_uint32),
        ("dwFVFCaps", c_uint32),
        ("dwTextureOpCaps", c_uint32),
        ("wMaxTextureBlendStages", c_uint16),
        ("wMaxSimultaneousTextures", c_uint16),
        ("dwMaxActiveLights", c_uint32),
        ("dvMaxVertexW", c_float),
        ("deviceGUID", GUID),
        ("wMaxUserClipPlanes", c_uint16),
        ("wMaxVertexBlendMatrices", c_uint16),
        ("dwVertexProcessingCaps", c_uint32),
        ("dwReserved1", c_uint32),
        ("dwReserved2", c_uint32),
        ("dwReserved3", c_uint32),
        ("dwReserved4", c_uint32),
    ]


D3DENUMDEVICESCALLBACK7 = WINFUNCTYPE(c_int32, c_void_p, c_void_p, c_void_p, c_void_p)

IDirect3D7EnumDevicesProto = WINFUNCTYPE(c_int32, c_void_p, D3DENUMDEVICESCALLBACK7, c_void_p)
