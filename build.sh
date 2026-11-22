#!/bin/bash
# Pure Python: the syntax of the scripts and the tests of the data side (no GUI, no phone).
set -euo pipefail
cd /project/apps/copyparty-hildon
for f in copyparty_hildon.py copyparty-hildon tests/make_demo.py; do
    python3 -I -c "import ast,sys; ast.parse(open('$f').read())"
done
python3 -I tests/test_copyparty_hildon.py > /tmp/copyparty-hildon-test.log 2>&1 || { cat /tmp/copyparty-hildon-test.log; exit 1; }
echo "copyparty-hildon: syntax ok, $(grep -E '^Ran ' /tmp/copyparty-hildon-test.log) $(tail -n 1 /tmp/copyparty-hildon-test.log)"
