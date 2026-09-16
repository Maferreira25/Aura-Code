#!/usr/bin/env python3
from pathlib import Path
import json, math, sys, collections, statistics

def wilson(k,n,z=1.96):
    if n==0: return (None,None)
    p=k/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return max(0,center-half),min(1,center+half)

path=Path(sys.argv[1]) if len(sys.argv)>1 else Path("validation/results")
files=list(path.glob("*.json")) if path.is_dir() else [path]
rows=[]
for f in files:
    try: rows.append(json.loads(f.read_text(encoding="utf-8")))
    except Exception as e: print("skip",f,e,file=sys.stderr)

by=collections.defaultdict(list)
for r in rows: by[r["arm"]].append(r)

print("Runs:",len(rows))
for arm in ["A0","A1","A2"]:
    rs=by.get(arm,[])
    k=sum(bool(r.get("qualified_success")) for r in rs); n=len(rs)
    lo,hi=wilson(k,n)
    if n:
        print(f"{arm}: QS {k}/{n} = {k/n:.3f} (Wilson 95% CI {lo:.3f}..{hi:.3f})")
        dims=collections.defaultdict(list)
        for r in rs:
            for d,v in r.get("dimensions",{}).items():
                if isinstance(v,(int,float)): dims[d].append(v)
        print("  dimensions:",", ".join(f"{d}={statistics.mean(v):.3f}" for d,v in sorted(dims.items())))

pairs=collections.defaultdict(dict)
for r in rows:
    if r.get("pair_id"):
        pairs[r["pair_id"]][r["arm"]]=r
diff=[]
for pid,p in pairs.items():
    if "A0" in p and "A2" in p:
        diff.append(int(p["A2"]["qualified_success"])-int(p["A0"]["qualified_success"]))
if diff:
    print(f"Matched A2-A0 QS difference: mean={statistics.mean(diff):.3f} over {len(diff)} pairs")
else:
    print("No matched A0/A2 pair_id data.")
