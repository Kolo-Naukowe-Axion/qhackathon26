#!/usr/bin/env python3
"""Render the checked presentation script with a local, stock synthetic voice.

Requires kokoro-onnx==0.6.1, onnxruntime, numpy, soundfile and ffmpeg.
Model: Kokoro-82M v1.0 ONNX; stock voice am_fenrir (no voice cloning).
Model files are supplied explicitly, never downloaded by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro


ROOT = Path(__file__).resolve().parents[1]
RATE = 24_000


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def spoken_text(text: str) -> str:
    """Pronunciation only: the source narration remains the caption text."""
    replacements = {
        "Axion": "Ack see on", "QAOA": "Q, A, O, A", "Main A": "Main A,",
        "VQE": "vee cue ee", "QUBO": "cue bow",
        "VeloxQ": "Velox Q", "CVaR": "C var", "XY": "ex why",
        "S0/S1": "S zero and S one", "S2/S3": "S two and S three",
        "S0": "S zero", "S1": "S one", "S2": "S two", "S3": "S three",
        "C1": "C one", "C2": "C two", "CP": "C P",
    }
    for original, replacement in replacements.items():
        text = re.sub(rf"\b{re.escape(original)}\b", replacement, text)
    return text


def sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if part.strip()]


def stamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole:02d},{milliseconds:03d}"


def retime(audio: np.ndarray, factor: float) -> np.ndarray:
    if factor <= 1.00001:
        return audio
    with tempfile.TemporaryDirectory(prefix="axion-voice-") as directory:
        source, target = (Path(directory) / name for name in ("source.wav", "target.wav"))
        sf.write(source, audio, RATE, subtype="FLOAT")
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", str(source),
            "-af", f"atempo={factor:.9f}", "-ar", str(RATE), str(target),
        ], check=True)
        result, rate = sf.read(target, dtype="float32")
        assert rate == RATE
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", type=Path, default=ROOT / "scripts/catering-showcase/story.json")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--voice", default="am_fenrir")
    parser.add_argument("--speed", type=float, default=1.03)
    parser.add_argument("--max-stretch", type=float, default=1.12)
    parser.add_argument("--output", type=Path, default=ROOT / "output/submission-final")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if args.max_stretch < 1 or args.max_stretch > 1.2:
        raise ValueError("Use gentle time adjustment: max stretch must be in [1, 1.2].")
    story_hash = digest(args.story)
    story = json.loads(args.story.read_text())
    folder = args.output / "audio"
    folder.mkdir(parents=True, exist_ok=True)
    model_hash, voices_hash = digest(args.model), digest(args.voices)
    options = ort.SessionOptions()
    options.intra_op_num_threads = args.threads
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(args.model), sess_options=options, providers=["CPUExecutionProvider"])
    engine = Kokoro.from_session(session, str(args.voices))
    if args.voice not in engine.get_voices():
        raise ValueError(f"Unknown stock voice: {args.voice}")
    manifest = {
        "synthetic_voice": True, "voice_cloning": False,
        "engine": "kokoro-onnx", "engine_version": importlib.metadata.version("kokoro-onnx"),
        "model": "Kokoro-82M v1.0", "model_sha256": model_hash,
        "attribution": {
            "model_author": "hexgrad / Kokoro contributors",
            "model_license": "Apache-2.0",
            "model_source": "https://huggingface.co/hexgrad/Kokoro-82M",
            "engine_author": "thewh1teagle / kokoro-onnx contributors",
            "engine_license": "MIT",
            "engine_source": "https://github.com/thewh1teagle/kokoro-onnx",
        },
        "voices_sha256": voices_hash, "stock_voice": args.voice, "speed": args.speed,
        "sample_rate": RATE, "story_sha256": story_hash,
        "story": str(args.story.relative_to(ROOT)) if args.story.is_relative_to(ROOT) else str(args.story),
        "caption_timing": "Exact generated sentence boundaries, adjusted for documented chapter time stretch.",
        "chapters": [],
    }
    total_duration = sum(float(chapter["duration"]) for chapter in story)
    track = np.zeros(round(total_duration * RATE), dtype=np.float32)
    captions = []
    chapter_start = 0.0
    for chapter in story:
        clips = []
        segment_records = []
        for index, sentence in enumerate(sentences(chapter["narration"])):
            spoken = spoken_text(sentence)
            cache_key = hashlib.sha256(json.dumps([spoken, args.voice, args.speed, model_hash, voices_hash]).encode()).hexdigest()[:16]
            filename = f"{chapter['id']}-{index + 1:02d}-{cache_key}.wav"
            path = folder / filename
            if path.exists():
                audio, rate = sf.read(path, dtype="float32")
            else:
                audio, rate = engine.create(spoken, voice=args.voice, speed=args.speed, lang="en-us", sentence_pause=0.15, clause_pause=0.08)
                sf.write(path, audio, rate, subtype="PCM_16")
                # First generation and cache reuse must use identical PCM samples.
                audio, rate = sf.read(path, dtype="float32")
            if rate != RATE or audio.ndim != 1 or not np.isfinite(audio).all():
                raise ValueError(f"Invalid generated audio: {path}")
            # Short fades avoid discontinuities without removing meaningful consonants.
            audio = audio.copy()
            fade = min(120, len(audio) // 4)
            audio[:fade] *= np.linspace(0, 1, fade)
            audio[-fade:] *= np.linspace(1, 0, fade)
            clips.append(audio)
            segment_records.append({"text": sentence, "tts_text": spoken, "source_wav": f"audio/{filename}", "natural_duration": len(audio) / RATE})
        gap = 0.15
        lead = 0.22
        available = float(chapter["duration"]) - lead - 0.25
        raw_duration = sum(len(clip) for clip in clips) / RATE + gap * (len(clips) - 1)
        factor = max(1.0, raw_duration / available)
        if factor > args.max_stretch + 1e-6:
            raise ValueError(f"Chapter {chapter['id']} needs {factor:.3f}x speed; shorten the narration or increase its duration. Cached audio retained.")
        chapter_audio = []
        offset = lead
        for index, (clip, record) in enumerate(zip(clips, segment_records)):
            adjusted = retime(clip, factor)
            duration = len(adjusted) / RATE
            start, end = chapter_start + offset, chapter_start + offset + duration
            record.update(start_seconds=round(start, 4), end_seconds=round(end, 4), stretch=factor)
            captions.append((start, end, record["text"]))
            chapter_audio.append(adjusted)
            offset += duration
            if index < len(clips) - 1:
                silence = np.zeros(round(gap / factor * RATE), dtype=np.float32)
                chapter_audio.append(silence)
                offset += len(silence) / RATE
        combined = np.concatenate(chapter_audio)
        # atempo may add a few milliseconds; enforce the declared end after the speech.
        position = round((chapter_start + lead) * RATE)
        if position + len(combined) > round((chapter_start + float(chapter["duration"])) * RATE):
            raise ValueError(f"Audio escaped chapter: {chapter['id']}")
        track[position:position + len(combined)] = combined
        sf.write(folder / f"{chapter['id']}.wav", np.pad(combined, (round(lead * RATE), max(0, round(float(chapter['duration']) * RATE) - len(combined) - round(lead * RATE)))), RATE, subtype="PCM_16")
        manifest["chapters"].append({
            "id": chapter["id"], "start_seconds": chapter_start,
            "duration": chapter["duration"], "natural_speech_seconds": round(raw_duration, 4),
            "time_stretch": round(factor, 6), "segments": segment_records,
        })
        chapter_start += float(chapter["duration"])
        print(f"{chapter['id']}: {raw_duration:.2f}s natural / {chapter['duration']}s chapter; {factor:.3f}x", flush=True)
    if digest(args.story) != story_hash:
        raise RuntimeError("Story changed during generation; rerun against the finished script.")
    peak = float(np.max(np.abs(track)))
    gain = 0.88 / peak if peak else 1.0
    track *= gain
    final = args.output / "voiceover.wav"
    temporary_audio = final.with_name("voiceover.pending.wav")
    sf.write(temporary_audio, track, RATE, subtype="PCM_16")
    temporary_audio.replace(final)
    subtitle_lines = []
    for index, (start, end, sentence) in enumerate(captions, 1):
        subtitle_lines.extend([str(index), f"{stamp(start)} --> {stamp(end)}", "\n".join(textwrap.wrap(sentence, width=70)), ""])
    (args.output / "captions.srt").write_text("\n".join(subtitle_lines))
    manifest.update(duration_seconds=len(track) / RATE, peak=float(np.max(np.abs(track))),
                    rms=float(np.sqrt(np.mean(track ** 2))), gain=gain, audio_sha256=digest(final))
    (args.output / "voice-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(final), "seconds": len(track) / RATE, "peak": manifest["peak"], "sentences": len(captions)}), flush=True)


if __name__ == "__main__":
    main()
