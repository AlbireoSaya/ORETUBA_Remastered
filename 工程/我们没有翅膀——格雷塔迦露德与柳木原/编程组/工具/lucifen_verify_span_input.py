def validate_span_input(expected, actual, width, height, spans):
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError
    total = width * height
    if total > 16000000:
        raise ValueError
    if not isinstance(expected, (bytes, bytearray)) or not isinstance(actual, (bytes, bytearray)):
        raise ValueError
    if len(expected) != total * 4 or len(actual) != total * 4:
        raise ValueError
    try:
        spans = list(spans)
    except TypeError:
        raise ValueError
    result = []
    prev = None
    for item in spans:
        try:
            item = list(item)
        except TypeError:
            raise ValueError
        if len(item) != 3:
            raise ValueError
        y, left, right = item
        if type(y) is not int or type(left) is not int or type(right) is not int:
            raise ValueError
        if not (0 <= y < height and 0 <= left < right <= width):
            raise ValueError
        if prev is not None:
            py, _, pr = prev
            if y < py or (y == py and left < pr):
                raise ValueError
        result.append((y, left, right))
        prev = (y, left, right)
    return result
