from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze

code = open("analyze.py").read()
print(f"SLOC: {analyze(code).sloc}, MI: {mi_visit(code, multi=True):.2f}")
for b in cc_visit(code):
    print(f"Function `{b.name}`: CC={b.complexity}, Length={getattr(b, 'endline', b.lineno) - b.lineno + 1}")