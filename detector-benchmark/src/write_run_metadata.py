#!/usr/bin/env python3
import argparse, json, os, pathlib, subprocess, time
p=argparse.ArgumentParser()
p.add_argument('--run-dir', required=True); p.add_argument('--run-id', required=True)
p.add_argument('--model-index', type=int, required=True); p.add_argument('--models-config', required=True)
p.add_argument('--device-env', required=True)
a=p.parse_args()
rd=pathlib.Path(a.run_dir); rd.mkdir(parents=True, exist_ok=True)
models=json.load(open(a.models_config)); model=models[a.model_index]
device={}
env_file = pathlib.Path(a.device_env)
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k,v=line.split('=',1); device[k]=v
def cmd(c):
    try: return subprocess.check_output(c, shell=True, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as e: return f'ERROR: {e}'
meta={
    'run_id': a.run_id,
    'utc_start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'model': model,
    'device': device,
    'environment': {
        'hostname': cmd('hostname'),
        'kernel': cmd('uname -a'),
        'hailortcli': cmd('command -v hailortcli && hailortcli --version || true'),
        'hailo_scan': cmd('hailortcli scan || true'),
        'python': cmd('python3 --version'),
        'git_commit': cmd('git rev-parse --short HEAD 2>/dev/null || true')
    }
}
(rd/'environment.json').write_text(json.dumps(meta, indent=2))
(rd/'config.json').write_text(json.dumps(model, indent=2))
