import subprocess, sys, os
P = "src/tesserae/widgets/navigation.py"
src = open(P).read()
M = [
    ("if start <= 2:", "if start <= 1:"),
    ("if start + run - 1 >= page_count - 3:", "if start + run - 1 >= page_count - 2:"),
    ("start = current - (run - 1) // 2", "start = current - run // 2"),
    ("if page_count <= slots:\n        return list(range(page_count))", "if page_count < slots:\n        return list(range(page_count))"),
    ("        if focused:  # the page", "        if False:  # the page"),
    ("node.set(focusable=not gap, a11y_hidden=gap,", "node.set(focusable=True, a11y_hidden=gap,"),
    ("focusable=not gap, a11y_hidden=gap,", "focusable=not gap, a11y_hidden=False,"),
    ('cursor="default" if gap else "pointer"', 'cursor="pointer"'),
    ('label="" if gap else f"Page {page + 1}")', 'label="")'),
    ('widget.interaction(f"{slot}{k}").enabled = not gap', 'pass'),
    ("if page is None or not", "if not"),
    ("or max_visible < 5:", "or max_visible < 4:"),
    ("windowed = page_count > max_visible", "windowed = page_count >= max_visible"),
    ('set(text="…" if gap else str(page + 1))', 'set(text="…" if gap else str(page))'),
]
bad = []
try:
    for a, b in M:
        assert src.count(a) == 1, a
        open(P, "w").write(src.replace(a, b))
        r = subprocess.run([".venv/bin/python", "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
                            "tests/test_pagination_ellipsis.py", "tests/test_segmented_pagination.py"],
                           capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        print("caught " if r.returncode else "SURVIVED", b[:60]); 
        if not r.returncode: bad.append(b)
finally:
    open(P, "w").write(src)
print(len(M) - len(bad), "/", len(M))
