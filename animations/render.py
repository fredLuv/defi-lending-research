"""Render checked current-product results; preserve input/output provenance."""
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from lending_story import ROOT,evidence,KEYS
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rates,costs,snapshot,old=evidence()
    output=HERE/'usdc_yield_liquidity.mp4'
    cmd=[str(Path(sys.executable).with_name('manimgx')),'render',str(HERE/'lending_story.py'),'-o',str(output),'-r','1920x1080','--fps','30','--crf','20']
    start=time.monotonic();subprocess.run(cmd,check=True,cwd=ROOT)
    subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(output),'-ss','6','-frames:v','1',str(HERE/'preview.png')],check=True)
    inputs=['reports/current_rates.csv','reports/current_scenarios.csv','data/current_manifest.json',
            'data/processed/daily_panel.csv','animations/lending_story.py','animations/requirements.lock']
    manifest=dict(engine='ManimGX',version=importlib.metadata.version('manimgx'),python=platform.python_version(),
        duration_seconds=38.1,resolution=[1920,1080],fps=30,render_command_wall_seconds=round(time.monotonic()-start,3),
        input_sha256={p:sha(ROOT/p) for p in inputs},video_sha256=sha(output),
        current_quote_rates={k:float(v['quote_rate']) for k,v in rates.items()},
        ninety_day_base_extra_usd={k:float(costs[k]['extra_vs_sgov']) for k in KEYS},
        snapshot_finished_utc=snapshot['finished_utc'],historical_aave_v3_cash_usdc=float(old['capacity_usdc']),
        sources=['../docs/DATA_SOURCES.md#current-v4v2-snapshot','../data/current_manifest.json','../data/manifest.json'],
        interpretation='Current V4/V2 quotes use different rate windows from SGOV SEC yield. Cost scenarios are not forecasts. April V3 cash is separate historical context; capacity is not guaranteed withdrawal.')
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
