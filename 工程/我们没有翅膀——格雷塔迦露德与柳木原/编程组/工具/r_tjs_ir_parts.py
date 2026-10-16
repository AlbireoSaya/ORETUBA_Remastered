from lucifen_literal_run_reference import literal_run


def island_vectors(raw, parts):
    """Yield only literal-island vectors; header/record execution is not claimed."""
    parts = list(parts)
    prev = 0
    for p in parts:
        try:
            kind, start, end = p["kind"], p["start"], p["end"]
        except (KeyError, TypeError, IndexError):
            raise ValueError("invalid part") from None
        if kind not in ("header", "record", "island"):
            raise ValueError("invalid kind")
        if type(start) is not int or type(end) is not int:
            raise ValueError("invalid offset type")
        if start != prev or end <= start or end > len(raw):
            raise ValueError("invalid partition")
        prev = end
    if prev != len(raw):
        raise ValueError("incomplete partition")

    for p in parts:
        if p["kind"] == "island":
            start, end = p["start"], p["end"]
            yield {
                "data": raw[start:end],
                "base": start,
                "result": literal_run(raw, start, end),
            }