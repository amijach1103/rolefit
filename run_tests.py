#!/usr/bin/env python3
"""Run the gate tests with no test framework installed. Standard library only."""
import importlib.util, sys, traceback
spec = importlib.util.spec_from_file_location("t", "tests/test_gates.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
tests = [(n, f) for n, f in vars(m).items() if n.startswith("test_") and callable(f)]
passed = failed = 0
for name, fn in tests:
    try:
        fn(); print(f"  PASS  {name}"); passed += 1
    except Exception as e:
        print(f"  FAIL  {name}  ({type(e).__name__})"); traceback.print_exc(limit=1); failed += 1
print(f"\n{passed} passed, {failed} failed, of {len(tests)}")
sys.exit(1 if failed else 0)
