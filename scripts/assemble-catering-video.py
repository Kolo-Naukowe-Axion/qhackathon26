#!/usr/bin/env python3
"""Assemble an edited video from actual UI captures and the local voice track.

Captures are made through the browser UI, including a real local sampling launch.
This script does not drive a browser, train a model or call a solver service.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'output/submission-final')
    args = parser.parse_args()
    folder = args.directory.resolve()
    story = json.loads((ROOT/'scripts/catering-showcase/story.json').read_text())
    voice = json.loads((folder/'voice-manifest.json').read_text())
    assert voice['story_sha256'] == sha(ROOT/'scripts/catering-showcase/story.json'), 'Stale voice script'
    capture = json.loads((folder/'capture-frames.json').read_text())
    frames = {}
    for frame in capture['frames']:
        time = frame['time']
        # Superseded boundary stills were made before the narration-aligned switch.
        if time in [76.3, 104.8]:
            continue
        if 26 <= time < 50 and len(frame['file']) != len('frame-02600.jpg'):
            continue
        time = {4.1: 4.0, 9.1: 9.0, 75.1: 75.0}.get(time, time)
        frames[time] = folder/'frames'/frame['file']
    # These are screenshots before, during and after the same real launch.
    # Holds are editorial reading time, not measurements of solver runtime.
    frames[139] = folder/'frames/launch-action.jpg'
    frames[140] = folder/'frames/launch-checked.jpg'
    ordered = sorted(frames.items())
    total = sum(c['duration'] for c in story)
    assert ordered[0][0] == 0 and total <= 300
    concat = ['ffconcat version 1.0']
    for index, (time, path) in enumerate(ordered):
        assert path.is_file(), path
        end = ordered[index+1][0] if index+1 < len(ordered) else total
        assert end > time
        # All paths are local, controlled capture names, never shell-expanded.
        escaped = str(path).replace("'", "'\\''")
        concat += [f"file '{escaped}'", f'duration {end-time:.6f}']
    concat += [f"file '{ordered[-1][1]}'"]
    (folder/'edit.ffconcat').write_text('\n'.join(concat)+'\n')
    chapters = [';FFMETADATA1', 'title=Axion Kitchen — QPoland Quantum Hackathon 2026',
                'comment=Stock synthetic narration. Edited captures of the actual UI; local launch and checked receipt retained.']
    cursor = 0
    for chapter in story:
        chapters += ['[CHAPTER]', 'TIMEBASE=1/1000', f'START={round(cursor*1000)}',
                     f'END={round((cursor+chapter["duration"])*1000)}', f'title={chapter["title"]}']
        cursor += chapter['duration']
    (folder/'chapters.ffmeta').write_text('\n'.join(chapters)+'\n')
    destination = folder/'axion-kitchen.mp4'
    command = ['ffmpeg','-hide_banner','-loglevel','warning','-y',
               '-f','concat','-safe','0','-i',str(folder/'edit.ffconcat'),
               '-i',str(folder/'voiceover.wav'),'-i',str(folder/'captions.srt'),
               '-i',str(folder/'chapters.ffmeta'),'-map','0:v:0','-map','1:a:0','-map','2:s:0',
               '-map_metadata','3','-map_chapters','3',
               '-vf','crop=1920:1080:0:0,fps=30,format=yuv420p',
               '-af','loudnorm=I=-16:TP=-1.5:LRA=11',
               '-c:v','libx264','-preset','medium','-crf','18','-threads','4',
               '-c:a','aac','-b:a','192k','-ar','48000','-c:s','mov_text',
               '-metadata:s:s:0','language=eng','-metadata:s:s:0','title=English',
               '-movflags','+faststart','-t',str(total),str(destination)]
    subprocess.run(command, check=True)
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format',
                                              '-show_streams','-show_chapters','-of','json',str(destination)]))
    video = next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['width'],video['height']) == (1920,1080)
    assert abs(float(probe['format']['duration'])-total)<.1
    assert any(s['codec_type']=='audio' for s in probe['streams'])
    assert any(s['codec_type']=='subtitle' for s in probe['streams'])
    assert len(probe['chapters']) == len(story)
    sources = ['scripts/catering-showcase/'+name for name in
               ['index.html','studio.js','studio.css','story.json','evidence.json','live-parameters.json','playback.js']]
    manifest = {'status':'local_export_verified','duration_seconds':total,'resolution':[1920,1080],
                'narration':'Kokoro stock af_heart synthetic voice; no voice cloning',
                'picture':'Edited real UI captures. Animated service captured at 5 fps; output 30 fps. Static model and result frames held for reading.',
                'launch':'Real browser button launch, RUNNING state and checked receipt captured; editorial holds do not measure runtime.',
                'training_runs':0,'veloxq_submissions':0,'physical_qpu_jobs':0,
                'source_commit_before_changes':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'source_sha256':{p:sha(ROOT/p) for p in sources},
                'media':{name:{'sha256':sha(folder/name),'bytes':(folder/name).stat().st_size}
                         for name in ['axion-kitchen.mp4','voiceover.wav','captions.srt','voice-manifest.json','launch-ui-receipt.json']},
                'frames':len(ordered),'ffprobe':probe,
                'publication':'Not submitted to organizer. Public video URL is separate from local export.'}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'video':str(destination),'duration':total,'bytes':destination.stat().st_size,'frames':len(ordered)},indent=2))


if __name__ == '__main__':
    main()
