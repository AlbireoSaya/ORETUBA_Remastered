import json

def numeric_line(row):
    return "RCheckValue(%d,%d,%d,%d);" % (
        row["op"], row["a"], row["b"], row["expected"]
    )

def literal_line(data, base, result):
    stop = result["stop"]
    if stop not in ("limit", "nul", "marker"):
        raise ValueError(f"invalid stop: {stop!r}")
    for u in result["units"]:
        w = int(u[1])
        if w not in (1, 2):
            raise ValueError(f"invalid unit width: {w}")
    hx = " ".join("%02X" % b for b in data)
    lit = f"<% {hx} %>" if hx else "<% %>"
    widths = "".join(str(int(u[1])) for u in result["units"])
    return 'RCheckLiteral(%s,%d,%d,%s,"%s");' % (
        lit, base, result["end"], json.dumps(stop), widths
    )