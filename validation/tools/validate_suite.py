#!/usr/bin/env python3
from pathlib import Path
import json, re, subprocess, sys

ROOT=Path(__file__).resolve().parents[2]
SCROOT=ROOT/"validation"/"scenarios"/"public"
catalog=json.loads((ROOT/"controls"/"catalog.json").read_text(encoding="utf-8"))
control_ids={c["id"] for c in catalog["controls"]}
errors=[]

required=["id","title","version","evaluation_mode","category","task_file","workspace_dir","protected_test_dir","blocking_dimensions","controls"]

metas=list(SCROOT.glob("*/scenario.json"))
ids=[]
automated=0
for mp in metas:
    m=json.loads(mp.read_text(encoding="utf-8")); ids.append(m.get("id"))
    for k in required:
        if k not in m: errors.append(f"{mp.parent.name}: missing {k}")
    if m.get("id")!=mp.parent.name:
        errors.append(f"{mp.parent.name}: directory/id mismatch")
    if not re.match(r"^[A-Z]{3}-[A-Z0-9]+-[0-9]{3}$",m.get("id","")):
        errors.append(f"{mp.parent.name}: invalid id format")
    for cid in m.get("controls",[]):
        if cid not in control_ids: errors.append(f"{m.get('id')}: unknown control {cid}")
    for relkey in ["task_file","workspace_dir","protected_test_dir"]:
        if not (mp.parent/m.get(relkey,"")).exists():
            errors.append(f"{m.get('id')}: missing {relkey} path")
    for rel in m.get("integrity_files",[]):
        if not (mp.parent/m["workspace_dir"]/rel).exists():
            errors.append(f"{m.get('id')}: integrity file missing {rel}")
    if m.get("evaluation_mode")=="automated":
        automated+=1

if len(ids)!=len(set(ids)):
    errors.append("Duplicate scenario IDs")

# Baseline validation: public tests pass, protected tests fail for each automated seeded scenario.
cp=subprocess.run([sys.executable,str(ROOT/"validation"/"tools"/"harness.py"),"baseline","--isolation","local"],
                  cwd=ROOT,text=True,capture_output=True)
if cp.returncode!=0:
    errors.append("Baseline seeded-defect validation failed:\n"+cp.stdout+"\n"+cp.stderr)

gold=subprocess.run([sys.executable,str(ROOT/"validation"/"tools"/"harness.py"),"gold","--isolation","local"],
                    cwd=ROOT,text=True,capture_output=True,timeout=180)
if gold.returncode!=0:
    errors.append("Reference-solution validation failed:\n"+gold.stdout+"\n"+gold.stderr)

print(f"Scenarios: {len(metas)} ({automated} automated)")
print("\nSeeded baselines:")
print(cp.stdout.strip())
print("\nReference solutions:")
print(gold.stdout.strip())

if errors:
    print("\nSUITE VALIDATION FAILED")
    for e in errors: print(" -",e)
    sys.exit(1)

print("\nSUITE VALIDATION PASSED")
