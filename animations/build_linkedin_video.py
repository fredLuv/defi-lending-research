"""Burn subtitles into an added band; never cover or crop the scientific chart.

Run with .venv-animation/bin/python. Requires ffmpeg/ffprobe and the existing
Voicebox MP4. Pillow and the bundled Noto Sans font are pinned in requirements.lock.
"""
import hashlib
import json
from pathlib import Path
import site
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
DISCLAIMER='For educational purposes only · Not financial advice'

def stamp(seconds):
    ms=round(seconds*1000)
    return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'

def main():
    source=HERE/'usdc_yield_liquidity_voicebox.mp4'
    output=HERE/'usdc_lending_linkedin.mp4'
    cues=json.loads((HERE/'linkedin_captions.json').read_text())
    duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries',
                   'format=duration','-of','csv=p=0',str(source)],text=True))
    font_path=next(p for folder in site.getsitepackages() for p in Path(folder).rglob('*.ttf')
                   if p.name=='NotoSans[wght].ttf')
    font=ImageFont.truetype(str(font_path),48)
    small=ImageFont.truetype(str(font_path),32)
    assert all(0<=c['start']<c['end']<=duration for c in cues)
    assert all(a['end']<=b['start'] for a,b in zip(cues,cues[1:]))
    with tempfile.TemporaryDirectory(prefix='usdc-captions-') as tmp:
        folder=Path(tmp);inputs=[]
        cards=['']+[c['text'] for c in cues]
        for i,text in enumerate(cards):
            image=Image.new('RGB',(1920,240),'#17324A');draw=ImageDraw.Draw(image)
            lines=text.splitlines()
            assert len(lines)<=2
            for j,line in enumerate(lines):
                bounds=draw.textbbox((0,0),line,font=font)
                assert bounds[2]-bounds[0]<=1800, 'Subtitle exceeds safe horizontal margins'
                y=(72 if len(lines)==1 else 44)+j*64
                draw.text((960,y),line,font=font,fill='white',anchor='mm')
            draw.line((80,164,1840,164),fill='#496074',width=1)
            draw.text((960,202),DISCLAIMER,font=small,fill='#D8E2EB',anchor='mm')
            png=folder/f'{i:02d}.png';image.save(png)
            inputs+=['-loop','1','-framerate','1','-i',str(png)]
        filters=['[0:v]fps=30,pad=1920:1320:0:0:color=white[p]',
                 '[p][1:v]overlay=0:1080[b0]']
        for i,c in enumerate(cues):
            filters.append(f"[b{i}][{i+2}:v]overlay=0:1080:enable='gte(t,{c['start']})*lt(t,{c['end']})'[b{i+1}]")
        subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(source),*inputs,'-filter_complex',
                        ';'.join(filters),
                        '-map',f'[b{len(cues)}]','-map','0:a:0','-c:v','libx264','-crf','18','-preset','medium',
                        '-r','30','-pix_fmt','yuv420p','-c:a','copy','-t',str(duration),
                        '-movflags','+faststart',str(output)],check=True)
    srt='\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}\n' for i,c in enumerate(cues))
    (HERE/'linkedin_captions.srt').write_text(srt)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'source_sha256':sha(source),'captions_sha256':sha(HERE/'linkedin_captions.json'),
              'output_sha256':sha(output),'output_resolution':[1920,1320],
              'chart_region':[0,0,1920,1080],'subtitle_region':[0,1080,1920,240],
              'subtitle_font_px':48,'disclaimer_font_px':32,'disclaimer':DISCLAIMER,
              'audio':'copied unchanged','timing':'Phrase-level editorial cues; numbers normalized for reading.',
              'font_sha256':sha(font_path)}
    (HERE/'linkedin_video_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(output),'-ss','6',
                    '-frames:v','1',str(HERE/'linkedin_preview.png')],check=True)
    print(output)

if __name__=='__main__':main()
