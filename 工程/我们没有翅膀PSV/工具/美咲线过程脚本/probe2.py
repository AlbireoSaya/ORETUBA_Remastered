# -*- coding: utf-8 -*-
"""Probe 2: parse headers with cricodecs.Hca / .Adx to get real codec parameters."""
import os, sys, traceback

sys.path.insert(0, r"E:\ZCode Workspace\Galgame\工具\pylibs")
MEDIA = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\解密\PCSG00299\media"
os.chdir(MEDIA)

from cricodecs import awb as Cawb, cpk as Ccpk, hca as Chca, adx as Cadx

v = Cawb.load("VOICE.AWB")
bgm = Ccpk.load("BGM.AWB")
se = Ccpk.load("SE.AWB")

print("### VOICE.AWB (AFS2/AWB) — 3 samples")
for idx in (0, 1, 26499):
    d = v.file_bytes(idx)
    try:
        h = Chca.Hca.load_bytes(d)
        hd = h.header()
        print(f"  entry[{idx}] HCA v{hd.file.version} hdrsz={hd.file.header_size} "
              f"ch={hd.fmt.channel_count} sr={hd.fmt.sample_rate} frames={hd.fmt.frame_count} "
              f"enc={hd.cipher.encrypted} ciph_type={hd.cipher.type} samples={hd.sample_count} "
              f"comp={hd.codec.type} band={hd.codec.total_band_count}")
    except Exception as e:
        print(f"  entry[{idx}] HCA parse FAIL: {type(e).__name__}: {e}")

print("\n### BGM.AWB (CPK) — first/last")
for idx in (0, 1, 95):
    d = bgm.file_bytes(idx)
    try:
        a = Cadx.Adx.load_bytes(d)
        i = a.info()
        print(f"  entry[{idx}] ADX enc_mode={i.header.encoding_mode} bitdepth={i.header.bit_depth} "
              f"ch={i.header.channels} sr={i.header.sample_rate} samples={i.header.sample_count} "
              f"encrypted={i.is_encrypted} ahx={i.is_ahx} data_off={i.header.data_offset}")
    except Exception as e:
        print(f"  entry[{idx}] ADX parse FAIL: {type(e).__name__}: {e}")

print("\n### SE.AWB (CPK) — first/last")
for idx in (0, 1, 700):
    d = se.file_bytes(idx)
    tag = None
    try:
        a = Cadx.Adx.load_bytes(d)
        i = a.info()
        print(f"  entry[{idx}] ADX enc_mode={i.header.encoding_mode} bitdepth={i.header.bit_depth} "
              f"ch={i.header.channels} sr={i.header.sample_rate} samples={i.header.sample_count} "
              f"encrypted={i.is_encrypted} ahx={i.is_ahx}")
        tag = "adx"
    except Exception as e:
        print(f"  entry[{idx}] ADX parse FAIL: {type(e).__name__}: {e}")
    try:
        h = Chca.Hca.load_bytes(d)
        hd = h.header()
        print(f"  entry[{idx}] HCA v{hd.file.version} ch={hd.fmt.channel_count} sr={hd.fmt.sample_rate} "
              f"enc={hd.cipher.encrypted} ciph_type={hd.cipher.type} samples={hd.sample_count}")
        tag = "hca"
    except Exception as e:
        print(f"  entry[{idx}] HCA parse FAIL: {type(e).__name__}: {e}")

print("\n### decode smoke test (entry 0 of each source)")
try:
    wav = Chca.Hca.load_bytes(v.file_bytes(0)).decode()
    print("  VOICE[0] HCA.decode() ->", len(wav), "bytes, riff=", wav[:4])
except Exception as e:
    traceback.print_exc()
try:
    wav = Cadx.Adx.load_bytes(bgm.file_bytes(0)).decode()
    print("  BGM[0] ADX.decode() ->", len(wav), "bytes, riff=", wav[:4])
except Exception as e:
    traceback.print_exc()
try:
    wav = Cadx.Adx.load_bytes(se.file_bytes(0)).decode()
    print("  SE[0] ADX.decode() ->", len(wav), "bytes, riff=", wav[:4])
except Exception as e:
    traceback.print_exc()
