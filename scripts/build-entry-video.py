"""Build a local <=3 minute review draft from actual captured UI evidence.

Uses installed macOS speech and ffmpeg, no model APIs or network services.
Not a continuous screen recording: that is disclosed in the burned-in footer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]


def run(args):
    try:
        subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.decode(errors='replace')[-2000:])
        raise


def probe(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration',
                                          '-of','default=noprint_wrappers=1:nokey=1',str(path)]))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--voice',default='Daniel')
    parser.add_argument('--rate',type=int,default=190)
    parser.add_argument('--recording',type=Path,help='Actual timestamped browser frame capture for chapter 2')
    args=parser.parse_args()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    script=ROOT/'docs/STAGE2_VIDEO_SCRIPT.json'
    chapters=json.loads(script.read_text())
    font=ROOT/'presentation/assets/branding/manrope-semibold.ttf'
    footage=ROOT/'output/playwright/entry'
    durations=[]
    for i,chapter in enumerate(chapters):
        text=output/f'{i:02}.txt'
        text.write_text(chapter['text'])
        audio=output/f'{i:02}.aiff'
        run(['/usr/bin/say','-v',args.voice,'-r',str(args.rate),'-f',str(text),'-o',str(audio)])
        duration=probe(audio)+.7
        durations.append(duration)
        title=output/f'{i:02}-title.txt'
        title.write_text(chapter['title'])
        disclaimer=output/'disclosure.txt'
        disclaimer.write_text('Edited real UI captures / synthetic narration / local simulation / VeloxQ calls 0')
        # A near-square video preserves the readable full UI instead of making
        # its text tiny in a wide letterboxed canvas. No content is fabricated.
        # Generate a text-only video overlay; screenshot evidence is untouched.
        overlay=Image.new('RGBA',(1280,1200),(0,0,0,0))
        draw=ImageDraw.Draw(overlay)
        draw.rectangle((0,0,1280,61),fill='#263f4b')
        draw.rectangle((0,1147,1280,1200),fill='#263f4b')
        draw.text((24,15),chapter['title'],font=ImageFont.truetype(str(font),24),fill='white')
        draw.text((24,1165),disclaimer.read_text(),font=ImageFont.truetype(str(font),14),fill='white')
        overlay_path=output/f'{i:02}-overlay.png'
        overlay.save(overlay_path)
        input_args=['-loop','1','-framerate','24','-i',str(footage/chapter['image'])]
        if i==1 and args.recording:
            recording=args.recording.resolve()
            timestamps=json.loads((recording/'capture.json').read_text())['timestamps_ms']
            capture_list=output/'actual-button-action.ffconcat'
            entries=[]
            for k,t in enumerate(timestamps):
                entries.append(f"file '{recording/f'frame-{k:03}.png'}'\n")
                entries.append(f'duration {(timestamps[k+1]-t)/1000 if k+1<len(timestamps)else .1}\n')
            entries.append(f"file '{recording/f'frame-{len(timestamps)-1:03}.png'}'\n")
            capture_list.write_text(''.join(entries))
            input_args=['-f','concat','-safe','0','-i',str(capture_list)]
        filters=f'[0:v]fps=24,tpad=stop_mode=clone:stop_duration={duration},scale=1280:1084:force_original_aspect_ratio=decrease,pad=1280:1200:(ow-iw)/2:62:color=0x263f4b[screen];[screen][2:v]overlay=0:0[v]'
        run(['ffmpeg','-y','-loglevel','error',*input_args,
             '-i',str(audio),'-loop','1','-i',str(overlay_path),'-filter_complex',filters,
             '-map','[v]','-map','1:a','-af','apad=pad_dur=0.7','-t',str(duration),
             '-r','24','-fps_mode','cfr','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
             '-c:a','aac','-b:a','160k','-ar','48000','-ac','2',str(output/f'{i:02}.mp4')])
        print(json.dumps(dict(chapter=i+1,seconds=duration)),flush=True)
    if sum(durations)>179:
        raise ValueError(f'Draft exceeds safe three-minute budget: {sum(durations)}')
    listing=output/'concat.txt'
    listing.write_text(''.join(f"file '{i:02}.mp4'\n"for i in range(len(chapters))))
    video=output/'qfactoria-stage2-draft.mp4'
    run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),
         '-c','copy','-movflags','+faststart',str(video)])
    def stamp(seconds):
        ms=round(seconds*1000)
        return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    elapsed=0
    captions=[]
    for i,(chapter,duration)in enumerate(zip(chapters,durations)):
        # Chapter-length transcript cues are a review companion, not a claim of
        # word-aligned captions. The separate transcript remains editable.
        captions.append(f'{i+1}\n{stamp(elapsed)} --> {stamp(elapsed+duration)}\n{chapter["text"]}\n')
        elapsed+=duration
    (output/'transcript.srt').write_text('\n'.join(captions))
    (output/'script.json').write_bytes(script.read_bytes())
    receipt=dict(status='local review draft; not uploaded or submitted',duration_seconds=probe(video),
                 synthetic_voice=args.voice,speech_rate=args.rate,continuous_screen_recording=False,
                 video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),
                 narration_script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
                 screenshot_sha256={c['image']:hashlib.sha256((footage/c['image']).read_bytes()).hexdigest()for c in chapters},
                 physical_qpu_calls=0,veloxq_calls=0,review_required=True)
    if args.recording:
        receipt['actual_button_capture']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                         for p in args.recording.iterdir()if p.is_file()}
    assert receipt['duration_seconds']<=180
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
