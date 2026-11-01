import re

TARGET = (1956, 6)


def yr(y):
    y = int(y)
    return y if y >= 100 else (1900 + y if y >= 20 else 2000 + y)


def tok(t):
    """date token -> (earliest,latest) in months since year 0, or None if unknown; 'today' -> far future"""
    t = t.strip().rstrip(".")
    if re.fullmatch(r"today|present", t, re.I):
        return (10**6, 10**6)
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", t)
    if m:
        v = yr(m[3]) * 12 + int(m[2]) - 1
        return (v, v)
    m = re.fullmatch(r"(\d{1,2})\.(\d{2,4})", t)
    if m and 1 <= int(m[1]) <= 12:
        v = yr(m[2]) * 12 + int(m[1]) - 1
        return (v, v)
    m = re.fullmatch(r"(\d{4})", t)
    if m:
        return (int(m[1]) * 12, int(m[1]) * 12 + 11)
    return None


DT = r"(?:\d{1,2}\.\d{1,2}\.\d{2,4}|\d{1,2}\.\d{2,4}|\d{4}|today|present|\?)"
IV = re.compile(r"(" + DT + r")\s*(?:-|to|–)\s*(" + DT + r")")
T = TARGET[0] * 12 + TARGET[1] - 1


def status(a, b):
    """a,b tokens. returns yes/no/uncertain for covering June 1956"""
    A = tok(a) if a != "?" else None
    B = tok(b) if b != "?" else None
    if A is None and B is None:
        return "uncertain"
    if A and A[0] > T:
        return "no"
    if B and B[1] < T:
        return "no"
    if A and A[1] >= T:
        return "uncertain"  # start could be on/after June 56
    if B and B[0] <= T:
        return "uncertain"  # end could be on/before June 56
    if A is None or B is None:
        return "uncertain"
    return "yes"


def intervals(s):
    return IV.findall(s)


def cover(s):
    """best status over intervals in an item string, plus matched interval"""
    best = None
    iv = None
    rank = {"yes": 2, "uncertain": 1, "no": 0}
    for a, b in intervals(s):
        st = status(a, b)
        if best is None or rank[st] > rank[best]:
            best, iv = st, (a, b)
    return best, iv
