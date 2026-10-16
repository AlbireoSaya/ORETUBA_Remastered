from lucifen_glyph_gray8 import unpack_gray8_bitmap as u
import json
b=bytes([0,32,64,255,1,63,64,255])
r=u(b,3,2)
assert r["stride"]==4 and list(r["coverage_0_64"])==[0,32,64,1,63,64], r
try:
    u(bytes([0,32,65,255,1,63,64,255]),3,2)
    raise AssertionError("coverage65 accepted")
except ValueError:
    pass
z=u(b"",0,0)
assert z["stride"]==0 and list(z["coverage_0_64"])==[], z
try:
    u(b"",True,0)
    raise AssertionError("bool width accepted")
except ValueError:
    pass
try:
    u(bytes([0,32,64,255,1,63,64]),3,2)
    raise AssertionError("bad length accepted")
except ValueError:
    pass
try:
    u("bad",3,2)
    raise AssertionError("nonbytes accepted")
except ValueError:
    pass
ba=bytearray(b); before=ba[:]; u(ba,3,2); assert ba==before
print(json.dumps({"passed": True, "scope": "unpack_gray8_bitmap"}))