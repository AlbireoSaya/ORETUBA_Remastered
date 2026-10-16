def rect_union_spans(width, height, rects):
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive int")
    if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
        raise ValueError("height must be a positive int")
    try:
        rect_iter = list(rects)
    except TypeError:
        raise ValueError("rects must be iterable")
    checked = []
    for rect in rect_iter:
        try:
            vals = list(rect)
        except TypeError:
            raise ValueError("each rectangle must be iterable")
        if len(vals) != 4:
            raise ValueError("each rectangle must have exactly 4 ints")
        for v in vals:
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError("rectangle coordinates must be ints")
        left, top, right, bottom = vals
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError("rectangle out of bounds or empty")
        checked.append((left, top, right, bottom))
    if width * height > 16000000:
        raise ValueError("total pixels exceed 16000000")
    if not checked:
        return []
    rows = {}
    for left, top, right, bottom in checked:
        for y in range(top, bottom):
            rows.setdefault(y, []).append((left, right))
    result = []
    for y in sorted(rows):
        intervals = sorted(rows[y])
        cur_left, cur_right = intervals[0]
        for left, right in intervals[1:]:
            if left <= cur_right:
                if right > cur_right:
                    cur_right = right
            else:
                result.append((y, cur_left, cur_right))
                cur_left, cur_right = left, right
        result.append((y, cur_left, cur_right))
    return result
