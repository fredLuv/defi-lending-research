"""Use Voicebox's actual Kokoro backend with pinned weights and a preset voice."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
VOICEBOX_COMMIT='8af7efe62fab8d33e2a5dfbedabaa45f68a5184f'
MODEL_REVISION='f3ff3571791e39611d31c381e3a41a3af07b4987'
VOICE='af_heart'
REPO='hexgrad/Kokoro-82M'
CHECKOUT=ROOT/'.cache/voicebox'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.check_output(args,text=True).strip()
def stamp(seconds):
    ms=round(seconds*1000)
    return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'

async def main():
    assert run(['git','-C',str(CHECKOUT),'rev-parse','HEAD'])==VOICEBOX_COMMIT
    os.environ['OMP_NUM_THREADS']='4'
    sys.path.insert(0,str(CHECKOUT))
    import torch
    import soundfile as sf
    import espeakng_loader
    # eSpeak's native loader fails under this long project path. A temporary
    # short-path copy of its bundled dictionaries avoids the fallback to its
    # build-machine directory; no package files or system installation change.
    dictionaries=tempfile.TemporaryDirectory(prefix='voicebox-')
    short_path=Path(dictionaries.name)/'espeak-ng-data'
    shutil.copytree(espeakng_loader.get_data_path(),short_path)
    espeakng_loader.get_data_path=lambda:str(short_path)
    os.environ['ESPEAK_DATA_PATH']=str(short_path)
    os.environ['PHONEMIZER_ESPEAK_DATA_PATH']=str(short_path)
    from huggingface_hub import hf_hub_download
    from kokoro import KModel
    from backend.backends.kokoro_backend import KokoroTTSBackend
    torch.set_num_threads(4)
    files={name:Path(hf_hub_download(REPO,name,revision=MODEL_REVISION))
           for name in ['config.json','kokoro-v1_0.pth',f'voices/{VOICE}.pt']}
    backend=KokoroTTSBackend()
    # Supply pinned local model/voice files; generation and edge trimming use
    # Voicebox unmodified. Its normal lazy loader otherwise resolves main.
    backend._model=KModel(repo_id=REPO,config=str(files['config.json']),
                          model=str(files['kokoro-v1_0.pth'])).to('cpu').eval()
    chunks=json.loads((HERE/'voicebox_narration.json').read_text())
    cache=ROOT/'.cache/voicebox-narration';cache.mkdir(exist_ok=True)
    measured=[];inputs=[];filters=[];subtitles=[]
    for i,c in enumerate(chunks):
        key=hashlib.sha256((c['text']+VOICE+MODEL_REVISION+VOICEBOX_COMMIT).encode()).hexdigest()[:16]
        path=cache/f'{key}.wav'
        if not path.exists():
            audio,sr=await backend.generate(c['text'],{'preset_voice_id':str(files[f'voices/{VOICE}.pt'])},seed=42)
            sf.write(path,audio,sr)
        info=sf.info(path);duration=info.duration
        print(f'Segment {i+1}: {duration:.2f}s / {c["end"]-c["start"]:.2f}s available',flush=True)
        assert duration<=c['end']-c['start'], 'Shorten this segment; do not accelerate or truncate speech.'
        measured.append(dict(c,duration_seconds=duration,wav_sha256=sha(path)))
        inputs+=['-i',str(path)]
        filters.append(f'[{i+1}:a]adelay={round(c["start"]*1000)}:all=1[a{i}]')
        subtitles.append(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["start"]+duration)}\n{c["text"]}\n')
    labels=''.join(f'[a{i}]' for i in range(len(chunks)))
    filters.append(f'{labels}amix=inputs={len(chunks)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,apad,atrim=duration=38.134[out]')
    source=HERE/'usdc_yield_liquidity.mp4';output=HERE/'usdc_yield_liquidity_voicebox.mp4'
    run(['ffmpeg','-loglevel','error','-y','-i',str(source),*inputs,'-filter_complex',';'.join(filters),
         '-map','0:v:0','-map','[out]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000',
         '-movflags','+faststart',str(output)])
    (HERE/'voicebox_narration.srt').write_text('\n'.join(subtitles))
    manifest={'engine':'Voicebox KokoroTTSBackend','voicebox_commit':VOICEBOX_COMMIT,
              'model':REPO,'model_revision':MODEL_REVISION,'voice':VOICE,'voice_type':'synthetic preset',
              'device':'cpu','threads':4,'seed':42,'generation_speed':1.0,
              'model_file_sha256':{k:sha(v) for k,v in files.items()},'segments':measured,
              'source_video_sha256':sha(source),'output_sha256':sha(output),
              'script_sha256':sha(HERE/'voicebox_narration.json'),
              'video_stream':'copied unchanged','audio':'AAC, -16 LUFS target, -1.5 dBTP ceiling'}
    (HERE/'voicebox_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(output)

if __name__=='__main__':asyncio.run(main())
