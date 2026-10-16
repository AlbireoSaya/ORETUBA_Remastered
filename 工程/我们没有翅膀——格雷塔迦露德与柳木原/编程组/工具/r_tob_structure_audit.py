import sys, json, hashlib, struct
from pathlib import Path

ROOT = Path(r"E:/ZCode Workspace/Galgame")
TOOLS = ROOT / "工程" / "我们没有翅膀R" / "工具"
SCRIPT = ROOT / "工程" / "我们没有翅膀R" / "语料" / "R版SCRIPT"
sys.path.insert(0, str(TOOLS))
import tob_extract as te

rows = []
total_t = total_invalid = total_oor = 0
all_header = True
tob_files = sorted(SCRIPT.glob("*.tob"), key=lambda p: p.name)
if not tob_files:
    summary = {
        "expected_files": 418,
        "files": 0,
        "message_table_entries": 0,
        "all_header_size_match": True,
        "total_invalid_message_tails": 0,
        "total_out_of_range_labels": 0,
        "error_count": 0,
        "status": "FAIL",
        "performance_semantics_verified": False
    }
    print(json.dumps({"summary": summary, "rows": []}, ensure_ascii=False, indent=2))
    sys.exit(1)

for p in tob_files:
    data = p.read_bytes()
    row = {
        "name": p.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "code_start": None,
        "labels": [],
        "label_count": 0,
        "T_count": 0,
        "header_size_match": False,
        "out_of_range_label": [],
        "invalid_message_tail": []
    }
    try:
        h = te.parse_header(data)
        labels = h["labels"]
        T = h["T"]
        code_start = h["code_start"]
        label_end = h["label_end"]
        label_items = list(labels.items()) if isinstance(labels, dict) else list(labels)
        label_size = struct.unpack_from('<I', data, 4)[0]
        row.update(
            code_start=code_start,
            labels=label_items,
            label_count=len(label_items),
            T_count=len(T),
            header_size_match=(label_size + 4 == label_end)
        )
        if code_start > len(data):
            row["error"] = "code_start out of range"
        for item in label_items:
            name, addr = item if isinstance(item, (tuple, list)) and len(item) >= 2 else (None, item)
            if not (0 <= addr <= len(data) - code_start):
                row["out_of_range_label"].append({"name": str(name), "addr": addr})
        for k, t in enumerate(T):
            end = code_start + t
            if not (18 <= end - code_start) or end > len(data) or data[end-18:end-4] != te.TAIL_PREFIX or struct.unpack_from('<I', data, end-4)[0] != k:
                row["invalid_message_tail"].append(k)
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"
    rows.append(row)
    total_t += row["T_count"]
    total_invalid += len(row["invalid_message_tail"])
    total_oor += len(row["out_of_range_label"])
    all_header = all_header and row["header_size_match"]

error_count = sum(1 for r in rows if "error" in r)
status = "PASS" if (
    len(rows) == 418
    and error_count == 0
    and all_header
    and total_invalid == 0
    and total_oor == 0
) else "FAIL"

summary = {
    "expected_files": 418,
    "files": len(rows),
    "message_table_entries": total_t,
    "all_header_size_match": all_header,
    "total_invalid_message_tails": total_invalid,
    "total_out_of_range_labels": total_oor,
    "error_count": error_count,
    "status": status,
    "performance_semantics_verified": False
}
print(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
sys.exit(0 if status == "PASS" else 1)