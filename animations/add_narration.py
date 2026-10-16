"""Add local synthetic narration without re-encoding the scientific visuals.

Requires macOS say (Samantha), ffmpeg and ffprobe; no API or paid service.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent

def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True).stdout

def stamp(seconds):
    ms=round(seconds*1000)
    return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'

def main():
    for tool in ['say','ffmpeg','ffprobe']:
        if not shutil.which(tool):
            raise SystemExit(f'{tool} is required for this optional macOS voiceover.')
    script=HERE/'narration.json'
    chunks=json.loads(script.read_text())
    source=HERE/'usdc_yield_liquidity.mp4'
    output=HERE/'usdc_yield_liquidity_narrated.mp4'
    measured=[];subtitles=[]
    with tempfile.TemporaryDirectory() as tmp:
        inputs=[];filters=[]
        for i,chunk in enumerate(chunks):
            audio=Path(tmp)/f'{i}.aiff'
            # Fixed rate, no audio acceleration or truncated sentences.
            run(['say','-v','Samantha','-r','185','-o',str(audio),chunk['text']])
            duration=float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(audio)]))
            assert duration <= chunk['end']-chunk['start'], (i,duration,'Narration exceeds its scene')
            inputs+=['-i',str(audio)]
            filters.append(f'[{i+1}:a]adelay={round(chunk["start"]*1000)}:all=1[a{i}]')
            measured.append(dict(chunk,duration_seconds=duration))
            subtitles.append(f'{i+1}\n{stamp(chunk["start"])} --> {stamp(chunk["start"]+duration)}\n{chunk["text"]}\n')
        labels=''.join(f'[a{i}]' for i in range(len(chunks)))
        filters.append(f'{labels}amix=inputs={len(chunks)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,apad,atrim=duration=38.134[out]')
        run(['ffmpeg','-loglevel','error','-y','-i',str(source),*inputs,
             '-filter_complex',';'.join(filters),'-map','0:v:0','-map','[out]',
             '-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(output)])
    (HERE/'narration.srt').write_text('\n'.join(subtitles))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (HERE/'narration_manifest.json').write_text(json.dumps({
        'voice':'macOS Samantha (synthetic)','rate_words_per_minute':185,
        'source_video_sha256':sha(source),'script_sha256':sha(script),
        'output_sha256':sha(output),'segments':measured,
        'video_stream':'copied unchanged','audio':'AAC; -16 LUFS target, -1.5 dBTP ceiling',
        'note':'Voice rendering can differ by macOS version. Silent original is preserved.'
    },indent=2)+'\n')
    print(output)
    print(json.dumps(measured,indent=2))

if __name__=='__main__':main()
