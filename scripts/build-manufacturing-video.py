"""Local recovery-centered video from actual screenshots and macOS speech."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def run(args):
    result=subprocess.run(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace')[-2500:])
def duration(p):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)]))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    script=ROOT/'docs/STAGE2_MANUFACTURING_VIDEO_SCRIPT.json';chapters=json.loads(script.read_text());lengths=[]
    font=ROOT/'presentation/assets/branding/manrope-semibold.ttf'
    for i,c in enumerate(chapters):
        text=output/f'{i:02}.txt';text.write_text(c['text']);audio=output/f'{i:02}.aiff'
        run(['/usr/bin/say','-v','Daniel','-r','195','-f',str(text),'-o',str(audio)])
        seconds=duration(audio)+.5;lengths.append(seconds)
        overlay=Image.new('RGBA',(1280,1200));d=ImageDraw.Draw(overlay)
        d.rectangle((0,0,1280,60),fill='#263f4b');d.rectangle((0,1148,1280,1200),fill='#263f4b')
        d.text((22,16),c['title'],font=ImageFont.truetype(str(font),24),fill='white')
        d.text((22,1166),'Edited actual UI captures / synthetic narration / saved plans / VeloxQ calls 0',font=ImageFont.truetype(str(font),15),fill='white')
        layer=output/f'{i:02}-overlay.png';overlay.save(layer)
        run(['ffmpeg','-y','-loglevel','error','-loop','1','-framerate','24','-i',str(ROOT/c['image']),'-i',str(audio),'-loop','1','-i',str(layer),
             '-filter_complex','[0:v]scale=1280:1088:force_original_aspect_ratio=decrease,pad=1280:1200:(ow-iw)/2:60:color=0x263f4b[screen];[screen][2:v]overlay=0:0[v]',
             '-map','[v]','-map','1:a','-af','apad=pad_dur=0.5','-t',str(seconds),'-r','24','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2',str(output/f'{i:02}.mp4')])
        print(json.dumps(dict(chapter=i+1,seconds=seconds)),flush=True)
    assert sum(lengths)<179,'Shorten script before submitting'
    listing=output/'concat.txt';listing.write_text(''.join(f"file '{i:02}.mp4'\n"for i in range(len(chapters))))
    video=output/'qfactoria-manufacturing-review.mp4'
    run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(video)])
    (output/'script.json').write_bytes(script.read_bytes())
    receipt=dict(status='Local review draft; no upload or submission',duration_seconds=duration(video),synthetic_voice='Daniel',speech_rate=195,
                 continuous_recording=False,video_sha256=sha(video),script_sha256=sha(script),builder_sha256=sha(Path(__file__)),
                 source_captures={c['image']:sha(ROOT/c['image'])for c in chapters},chapter_seconds=lengths,veloxq_calls=0,physical_qpu_calls=0)
    assert receipt['duration_seconds']<180
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args();main(a.output)
