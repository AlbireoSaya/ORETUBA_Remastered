import json

from lucifen_guest_screen_point import decode_screen_point_lparam
from lucifen_guest_setcursor_message import map_setcursor_message

assert decode_screen_point_lparam(-1)==(-1,-1)
assert decode_screen_point_lparam(0x8000ffff)==(-1,-32768)
assert decode_screen_point_lparam(0x7fff7fff)==(32767,32767)
r=map_setcursor_message(0x100000001,0x02000001,0x100000001,0x69f50000)
assert r=={"guest_wparam":0x69f50000,"guest_lparam":0x02000001,"hit_test":1,"trigger_message":0x200},r
assert map_setcursor_message(0x100000001,0x0200ffff,0x100000001,0x69f50000)["hit_test"]==-1
for v in (True,"x",2**32,-2**31-1):
    try: decode_screen_point_lparam(v); raise AssertionError
    except ValueError: pass
for a in ((2,1,1,1),(True,1,True,1),(1,1,1,0)):
    try: map_setcursor_message(*a); raise AssertionError
    except ValueError: pass
print(json.dumps({"passed":True}))
