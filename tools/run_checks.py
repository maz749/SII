#!/usr/bin/env python3
"""Воспроизводимый запуск проверок с сохранением журналов."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
COMMANDS=[
 ('prolog_tests.txt',['swipl','-q','-s','tests/knowledge_base_tests.pl','-g','run_tests','-t','halt']),
 ('prolog_queries.txt',['swipl','-q','-s','lab1/queries.pl','-g','main','-t','halt']),
 ('python_tests.txt',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v']),
 ('ontology_build.txt',[sys.executable,'lab2/build_ontology.py']),
 ('ontology_check.txt',[sys.executable,'lab2/verify_ontology.py']),
]
for name,cmd in COMMANDS:
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    (ROOT/'evidence'/name).write_text(r.stdout+r.stderr)
    print(f'{name}: {"OK" if r.returncode==0 else "FAIL"}')
    if r.returncode:
        print(r.stdout+r.stderr)
        raise SystemExit(r.returncode)
