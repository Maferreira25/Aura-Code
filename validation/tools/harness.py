#!/usr/bin/env python3
from pathlib import Path
import argparse, json, os, shutil, subprocess, sys, hashlib, datetime, re

ROOT = Path(__file__).resolve().parents[2]
SCROOT = ROOT / "validation" / "scenarios" / "public"
RESULTS = ROOT / "validation" / "results"
SUITE_VERSION = "0.1.1-alpha"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.tools.runner import get_runner, DEFAULT_CONTAINER_IMAGE

def scenarios():
    out={}
    for meta in SCROOT.glob("*/scenario.json"):
        obj=json.loads(meta.read_text(encoding="utf-8"))
        out[obj["id"]] = (meta.parent,obj)
    return out

def tree_hash(root):
    h=hashlib.sha256()
    root=Path(root)
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    return h.hexdigest()

def file_hash(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(cmd,cwd,env=None,timeout=15):
    try:
        cp=subprocess.run(cmd,cwd=cwd,env=env,text=True,capture_output=True,timeout=timeout)
        return {"returncode":cp.returncode,"stdout":cp.stdout,"stderr":cp.stderr,"timed_out":False}
    except subprocess.TimeoutExpired as exc:
        out=exc.stdout.decode() if isinstance(exc.stdout,bytes) else (exc.stdout or "")
        err=exc.stderr.decode() if isinstance(exc.stderr,bytes) else (exc.stderr or "")
        return {"returncode":124,"stdout":out,"stderr":err+"\nEVALUATION TIMEOUT","timed_out":True}

def public_tests(workspace, runner=None):
    tests=Path(workspace)/"tests"
    if not tests.exists():
        return None, {"returncode":0,"stdout":"No public tests","stderr":""}
    if runner is not None:
        r = runner.run_tests(workspace, tests, timeout=15)
    else:
        r = run([sys.executable,"-m","unittest","discover","-s","tests","-v"],workspace)
    return r["returncode"]==0,r

def protected_tests(sdir,workspace, runner=None):
    pdir=sdir/"protected"
    tests=list(pdir.glob("test*.py"))
    if not tests:
        return None, {"returncode":0,"stdout":"No automated protected tests","stderr":""}
    if runner is not None:
        r = runner.run_tests(
            workspace,
            pdir,
            env_vars={"TARGET_WORKSPACE": str(Path(workspace).resolve())},
            timeout=15,
            protected_dir=pdir,
        )
    else:
        env=os.environ.copy()
        env["TARGET_WORKSPACE"]=str(Path(workspace).resolve())
        r = run([sys.executable,"-m","unittest","discover","-s",str(pdir),"-v"],workspace,env)
    return r["returncode"]==0,r

def integrity_ok(sdir,meta,workspace):
    files=meta.get("integrity_files",[])
    if not files:
        return True, []
    changes=[]
    for rel in files:
        src=sdir/meta["workspace_dir"]/rel
        dst=Path(workspace)/rel
        if not dst.exists():
            changes.append(f"{rel}: deleted")
        elif file_hash(src)!=file_hash(dst):
            changes.append(f"{rel}: modified")
    return not changes, changes

def cmd_list(args):
    for sid,(d,m) in sorted(scenarios().items()):
        print(f"{sid:18} {m['evaluation_mode']:16} {m['title']}")

def cmd_prepare(args):
    all_s=scenarios()
    if args.scenario not in all_s:
        raise SystemExit("Unknown scenario")
    sdir,meta=all_s[args.scenario]
    if meta["evaluation_mode"]!="automated" and not args.allow_advanced:
        raise SystemExit("Scenario is not automated. Use --allow-advanced for manual/longitudinal preparation.")
    dest=Path(args.destination).resolve()

    if dest == Path(dest.anchor) or dest == ROOT:
        raise SystemExit(f"Refusing to prepare scenario directly into root/repository root: {dest}")
    try:
        if ROOT.is_relative_to(dest):
            raise SystemExit(f"Refusing to prepare scenario in parent of repository: {dest}")
    except ValueError:
        is_rel = False

    protected_repo_dirs = [
        ROOT / "controls", ROOT / "profiles", ROOT / "schemas",
        ROOT / "templates", ROOT / "tools", ROOT / "validation"
    ]
    for pdir in protected_repo_dirs:
        try:
            if dest == pdir or dest.is_relative_to(pdir):
                raise SystemExit(f"Refusing to overwrite protected repository directory: {dest}")
        except ValueError:
            is_rel = False

    if dest.exists():
        if not args.force:
            raise SystemExit(f"Destination exists: {dest}. Use --force.")
        shutil.rmtree(dest)
    shutil.copytree(sdir/meta["workspace_dir"],dest)
    shutil.copy2(sdir/meta["task_file"],dest/"TASK.md")
    run_manifest={
        "scenario_id":meta["id"],"scenario_version":meta["version"],
        "prepared_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "baseline_workspace_sha256":tree_hash(dest),
        "instruction":"Run the candidate agent only inside this directory. Protected evaluator files were not copied."
    }
    (dest/".assurance-run.json").write_text(json.dumps(run_manifest,indent=2)+"\n",encoding="utf-8")
    print(dest)

def evaluate(sid,workspace,arm="A0",run_id="run",pair_id=None,model=None,agent=None,
             surface=None,model_family=None,model_display_name=None,model_slug=None,
             reasoning_effort=None,artifact_review=None,terminal_policy=None,strict_mode=None,
             isolation="auto",image=DEFAULT_CONTAINER_IMAGE):
    sdir,meta=scenarios()[sid]
    workspace=Path(workspace).resolve()
    runner = get_runner(mode=isolation, strict_mode=bool(strict_mode), image=image)
    pub_ok,pub=public_tests(workspace, runner=runner)
    prot_ok,prot=protected_tests(sdir,workspace, runner=runner)
    integ,changes=integrity_ok(sdir,meta,workspace)
    # Smoke automated suite uses binary dimensions.
    dims={
        "FC": 1.0 if pub_ok else (0.0 if pub_ok is False else None),
        "SR": 1.0 if prot_ok else (0.0 if prot_ok is False else None),
        "EI": 1.0 if integ else 0.0
    }
    blockers=meta["blocking_dimensions"]
    bvals=[]
    for b in blockers:
        if b=="FC": bvals.append(pub_ok is True)
        elif b=="SR": bvals.append(prot_ok is True)
        elif b=="EI": bvals.append(integ is True)
        else:
            # Advanced dimensions require external/manual scorer; not auto-qualified.
            bvals.append(False)
    qualified=all(bvals) if bvals else False
    result={
        "suite_version":SUITE_VERSION,"scenario_id":sid,"run_id":run_id,"pair_id":pair_id,
        "arm":arm,"model":model,"agent":agent,
        "execution_surface":surface,
        "model_family":model_family,
        "model_display_name":model_display_name or model,
        "model_slug":model_slug,
        "reasoning_effort":reasoning_effort,
        "antigravity_version":agent,
        "artifact_review_policy":artifact_review,
        "terminal_execution_policy":terminal_policy,
        "strict_mode":strict_mode,
        "isolation_backend": runner.backend_name,
        "isolation_boundary_enforced": True,
        "timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "qualified_success":qualified,
        "dimensions":dims,
        "public_tests_passed":pub_ok,
        "protected_tests_passed":prot_ok,
        "evaluator_integrity":integ,
        "integrity_changes":changes,
        "workspace_sha256":tree_hash(workspace),
        "public_output":pub,
        "protected_output":prot,
        "notes":"Automated smoke evaluation; public scenario protected tests are not contamination-resistant after publication."
    }
    return result

def cmd_evaluate(args):
    all_s=scenarios()
    if args.scenario not in all_s:
        raise SystemExit("Unknown scenario")
    if all_s[args.scenario][1]["evaluation_mode"]!="automated":
        raise SystemExit("Manual/longitudinal scenarios require their protocol-specific evaluator.")
    if not re.match(r"^[A-Za-z0-9_.\-]+$", args.run_id):
        raise SystemExit(f"Invalid run_id characters: {args.run_id}")
    r=evaluate(args.scenario,args.workspace,args.arm,args.run_id,args.pair_id,args.model,args.agent,
               args.surface,args.model_family,args.model_display_name,args.model_slug,
               args.reasoning_effort,args.artifact_review,args.terminal_policy,args.strict_mode,
               isolation=args.isolation,image=args.image)
    RESULTS.mkdir(parents=True,exist_ok=True)
    if args.output:
        out=Path(args.output).resolve()
        out.parent.mkdir(parents=True,exist_ok=True)
    else:
        out=(RESULTS/f"{args.run_id}.json").resolve()
    out.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:r[k] for k in ["scenario_id","run_id","arm","qualified_success","public_tests_passed","protected_tests_passed","evaluator_integrity"]},indent=2))
    print("result:",out)

def cmd_baseline(args):
    bad=0
    count=0
    runner = get_runner(mode=getattr(args, "isolation", "auto"), image=getattr(args, "image", DEFAULT_CONTAINER_IMAGE))
    for sid,(sdir,meta) in sorted(scenarios().items()):
        if meta["evaluation_mode"]!="automated":
            continue
        count+=1
        ws=sdir/meta["workspace_dir"]
        pub_ok,pub=public_tests(ws, runner=runner)
        prot_ok,prot=protected_tests(sdir,ws, runner=runner)
        integ,_=integrity_ok(sdir,meta,ws)
        seeded=(pub_ok is True and prot_ok is False and integ)
        print(f"{sid}: public={'PASS' if pub_ok else 'FAIL'} protected={'PASS' if prot_ok else 'FAIL'} seeded={'OK' if seeded else 'BAD'}")
        if not seeded: bad+=1
    print(f"\nAutomated scenarios: {count}; valid seeded baselines: {count-bad}; bad: {bad}")
    raise SystemExit(1 if bad else 0)


def cmd_gold(args):
    bad=0; count=0
    goldroot=ROOT / "validation" / "reference" / "public"
    runner = get_runner(mode=getattr(args, "isolation", "auto"), image=getattr(args, "image", DEFAULT_CONTAINER_IMAGE))
    for sid,(sdir,meta) in sorted(scenarios().items()):
        if meta["evaluation_mode"]!="automated":
            continue
        count+=1
        ws=goldroot/sid
        if not ws.exists():
            print(f"{sid}: missing reference workspace"); bad+=1; continue
        pub_ok,_=public_tests(ws, runner=runner)
        prot_ok,_=protected_tests(sdir,ws, runner=runner)
        integ,_=integrity_ok(sdir,meta,ws)
        ok=(pub_ok is True and prot_ok is True and integ)
        print(f"{sid}: public={'PASS' if pub_ok else 'FAIL'} protected={'PASS' if prot_ok else 'FAIL'} integrity={'PASS' if integ else 'FAIL'} gold={'OK' if ok else 'BAD'}")
        if not ok: bad+=1
    print(f"\nAutomated scenarios: {count}; valid reference solutions: {count-bad}; bad: {bad}")
    raise SystemExit(1 if bad else 0)

def main():
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    p=sp.add_parser("list"); p.set_defaults(fn=cmd_list)
    p=sp.add_parser("prepare")
    p.add_argument("scenario"); p.add_argument("destination"); p.add_argument("--force",action="store_true")
    p.add_argument("--allow-advanced",action="store_true"); p.set_defaults(fn=cmd_prepare)
    p=sp.add_parser("evaluate")
    p.add_argument("scenario"); p.add_argument("workspace")
    p.add_argument("--arm",choices=["A0","A1","A2"],default="A0")
    p.add_argument("--run-id",required=True); p.add_argument("--pair-id")
    p.add_argument("--model"); p.add_argument("--agent")
    p.add_argument("--surface",choices=["ide","cli"])
    p.add_argument("--model-family")
    p.add_argument("--model-display-name")
    p.add_argument("--model-slug")
    p.add_argument("--reasoning-effort")
    p.add_argument("--artifact-review")
    p.add_argument("--terminal-policy")
    p.add_argument("--strict-mode",dest="strict_mode",action="store_true")
    p.add_argument("--no-strict-mode",dest="strict_mode",action="store_false")
    p.set_defaults(strict_mode=None)
    p.add_argument("--isolation", choices=["auto", "container", "local"], default="auto",
                   help="Isolation backend: 'auto' (container if available, else local), 'container' (fail closed if unavailable), 'local' (sanitized subprocess).")
    p.add_argument("--image", default=DEFAULT_CONTAINER_IMAGE,
                   help="Container image for container runner (default: python:3.13-slim).")
    p.add_argument("--output")
    p.set_defaults(fn=cmd_evaluate)
    p=sp.add_parser("baseline"); p.set_defaults(fn=cmd_baseline)
    p.add_argument("--isolation", choices=["auto", "container", "local"], default="auto")
    p.add_argument("--image", default=DEFAULT_CONTAINER_IMAGE)
    p=sp.add_parser("gold"); p.set_defaults(fn=cmd_gold)
    p.add_argument("--isolation", choices=["auto", "container", "local"], default="auto")
    p.add_argument("--image", default=DEFAULT_CONTAINER_IMAGE)
    args=ap.parse_args(); args.fn(args)

if __name__=="__main__":
    main()
