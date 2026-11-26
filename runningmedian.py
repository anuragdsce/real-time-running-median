import sys
import time


class Heap:
    def __init__(self, is_max):
        self.data = []
        self.is_max = is_max

    def better(self, a, b):
        return a > b if self.is_max else a < b

    def push(self, value):
        self.data.append(value)
        i = len(self.data) - 1
        while i > 0:
            p = (i - 1) // 2
            if not self.better(self.data[i], self.data[p]):
                break
            self.data[i], self.data[p] = self.data[p], self.data[i]
            i = p

    def pop_root(self):
        root = self.data[0]
        last = self.data.pop()
        if not self.data:
            return root
        self.data[0] = last
        i = 0
        n = len(self.data)
        while 2*i+1 < n:
            child = 2*i+1
            right = child+1
            if right < n and self.better(self.data[right], self.data[child]):
                child = right
            if not self.better(self.data[child], self.data[i]):
                break
            self.data[i], self.data[child] = self.data[child], self.data[i]
            i = child
        return root

class Scoreboard:
    def __init__(self):
        self.lower = Heap(True)
        self.upper = Heap(False)
        self.low = self.lower.data
        self.high = self.upper.data
        self.history = []

    def add(self, score):
        if type(score) is not int or not -2**31 <= score < 2**31:
            raise ValueError('Score must be a signed 32-bit integer')
        if len(self.history) >= 100000:
            raise ValueError('Maximum 100,000 scores reached')
        if not self.low or score <= self.low[0]:
            self.lower.push(score)
        else:
            self.upper.push(score)
        if len(self.low) > len(self.high)+1:
            self.upper.push(self.lower.pop_root())
        elif len(self.high) > len(self.low):
            self.lower.push(self.upper.pop_root())
        m = self.median
        self.history.append((len(self.history)+1, score, m))
        return m

    @property
    def median(self):
        if not self.low:
            return None
        if len(self.low) == len(self.high):
            return (self.low[0]+self.high[0])/2
        return self.low[0]

def merge_sort(values):
    n = len(values)
    if n <= 1:
        return values[:]
    mid = n//2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    while i < len(left):
        out.append(left[i]); i += 1
    while j < len(right):
        out.append(right[j]); j += 1
    return out

def baseline(scores):
    seen, result = [], []
    for score in scores:
        seen.append(score)
        ordered = merge_sort(seen)
        n = len(ordered)
        result.append((ordered[(n-1)//2]+ordered[n//2])/2)
    return result


# ---------- display ----------
def fmt(m):
    """5.0 -> '5', 4.5 -> '4.5'."""
    return str(int(m)) if m == int(m) else str(m)


def print_table(history):
    print(f"{'#':>6} {'score':>12} {'median':>12}")
    for idx, score, m in history:
        print(f"{idx:>6} {score:>12} {fmt(m):>12}")


def print_summary(board):
    print(f"\ncount = {len(board.history)}   latest median = {fmt(board.median)}")


def text_graph(history, width=40):
    """Simple bar graph of the median history (bar length scaled to the range)."""
    meds = [m for _, _, m in history]
    lo, hi = min(meds), max(meds)
    span = (hi - lo) or 1
    print(f"\nMedian history graph (min {fmt(lo)}, max {fmt(hi)})")
    for idx, _, m in history:
        bar = "#" * (1 + int((m - lo) / span * (width - 1)))
        print(f"{idx:>6} | {bar} {fmt(m)}")


# ---------- input ----------
def parse_scores(text):
    return [int(tok) for tok in text.replace(",", " ").split()]


def replay_file(path):
    with open(path) as f:
        return parse_scores(f.read())


def run(scores, graph=False):
    board = Scoreboard()
    for s in scores:
        board.add(s)
    print_table(board.history)
    print_summary(board)
    if graph:
        text_graph(board.history)
    return board


# ---------- benchmark: heap vs. full re-sorting ----------
_seed = 12345

def next_rand():                      # tiny LCG, so no random module is needed
    global _seed
    _seed = (_seed * 1103515245 + 12345) % 2**31
    return _seed - 2**30


def bench():
    print(f"{'n':>8} {'heap (s)':>10} {'re-sort baseline (s)':>22}")
    for n in (500, 1000, 2000, 4000):
        data = [next_rand() for _ in range(n)]
        t0 = time.perf_counter()
        board = Scoreboard()
        got = [board.add(x) for x in data]
        t1 = time.perf_counter()
        base = baseline(data)
        t2 = time.perf_counter()
        assert got == base, "heap and baseline disagree"
        print(f"{n:>8} {t1 - t0:>10.4f} {t2 - t1:>22.4f}")
    t0 = time.perf_counter()
    board = Scoreboard()
    for _ in range(100000):
        board.add(next_rand())
    print(f"{100000:>8} {time.perf_counter() - t0:>10.4f} {'(too slow to run)':>22}")


# ---------- tests ----------
def medians(data):
    b = Scoreboard()
    return [b.add(x) for x in data]


def expect_error(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def test():
    results = []

    def check(name, cond):
        results.append(cond)
        print(("ok   - " if cond else "FAIL - ") + name)

    check("problem example [5,1,9,3] -> [5,3,5,4]", medians([5, 1, 9, 3]) == [5, 3, 5, 4])
    check("single item", medians([-8]) == [-8])
    check("repeated values", medians([2, 2, 2, 2]) == [2, 2, 2, 2])
    check("negative values", medians([-5, -1, -3]) == [-5, -3, -3])
    check("extremes, no overflow", medians([-2**31, 2**31 - 1]) == [-2**31, -0.5])
    check("empty board median is None", Scoreboard().median is None)

    ok = True
    for _ in range(200):
        n = 1 + (next_rand() % 60 + 60) % 60
        d = [next_rand() % 41 - 20 for _ in range(n)]
        ok = ok and medians(d) == baseline(d)
    check("200 random streams match the re-sort baseline", ok)

    check("rejects 2**31", expect_error(lambda: Scoreboard().add(2**31)))
    check("rejects -2**31 - 1", expect_error(lambda: Scoreboard().add(-2**31 - 1)))
    check("rejects float", expect_error(lambda: Scoreboard().add(3.5)))
    check("rejects bool", expect_error(lambda: Scoreboard().add(True)))

    b = Scoreboard()
    for i in range(100000):
        b.add(i)
    check("100,000 scores accepted", len(b.history) == 100000)
    check("100,001st score rejected", expect_error(lambda: b.add(1)))

    h = Heap(True)
    for v in (3, 9, 1, 7, 5):
        h.push(v)
    check("max-heap pops in descending order", [h.pop_root() for _ in range(5)] == [9, 7, 5, 3, 1])
    h = Heap(False)
    for v in (3, 9, 1, 7, 5):
        h.push(v)
    check("min-heap pops in ascending order", [h.pop_root() for _ in range(5)] == [1, 3, 5, 7, 9])

    print(f"\n{sum(results)}/{len(results)} checks passed")
    return all(results)


# ---------- demo + interactive ----------
def demo():
    print("Example from the problem statement: [5, 1, 9, 3]")
    run([5, 1, 9, 3])
    print("\nUnseen stream (negative, repeated, extreme values):")
    run([-7, -7, 2**31 - 1, 0, -2**31, 42, 42, 42, -1, 5], graph=False)
    print("\nExample [3, 5, 1, 6, 4] with graph:")
    run([3, 5, 1, 6, 4], graph=True)


def interactive():
    board = Scoreboard()
    print("Enter integer scores (q = quit, h = history table, g = graph).")
    for line in sys.stdin:
        line = line.strip()
        if line == "q":
            break
        if line == "h":
            print_table(board.history)
            continue
        if line == "g" and board.history:
            text_graph(board.history)
            continue
        try:
            for s in parse_scores(line):
                m = board.add(s)
                print(f"count = {len(board.history)}   latest median = {fmt(m)}")
        except ValueError as e:
            print("Invalid input:", e)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--demo":
        demo()
    elif arg == "--bench":
        bench()
    elif arg == "--test":
        sys.exit(0 if test() else 1)
    elif arg:
        run(replay_file(arg), graph=True)
    else:
        interactive()