"""Heuristics to detect low-effort or random-looking comment text."""


def _max_same_char_run(text):
    best = cur = 0
    prev = None
    for ch in text:
        if ch == prev:
            cur += 1
        else:
            cur = 1
            prev = ch
        best = max(best, cur)
    return best


def is_meaningless_comment_text(content):
    """
    Return True if text looks like noise: empty, single non-letter, all same char,
    very long identical runs, almost no distinct characters, or almost no letters.
    """
    s = (content or '').strip()
    if not s:
        return True
    if len(s) == 1:
        return not s[0].isalpha()
    # Require length >= 4 so pairs like repeated CJK ("谢谢") stay allowed.
    if len(s) >= 4 and len(set(s)) == 1:
        return True
    if _max_same_char_run(s) >= 14:
        return True
    n = len(s)
    letters = sum(1 for c in s if c.isalpha())
    if n >= 8 and letters == 0:
        return True
    if n >= 12 and len(set(s)) / n < 0.12:
        return True
    if n >= 14 and letters / n < 0.08:
        return True
    return False
