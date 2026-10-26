"""Turn each scene's text into a wav with macOS `say`, and measure it.

Writes docs/demo/audio/<id>.wav plus narration.json, which is the contract the
recorder and the assembler both read: the recorder uses the durations to decide
how long to linger, the assembler uses them to place the voice on the timeline.
"""

import json
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from demo_narration import RATE, SCENES, VOICE  # noqa: E402

import imageio_ffmpeg  # noqa: E402

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUT = Path(__file__).resolve().parents[1] / "docs" / "demo"
AUDIO = OUT / "audio"


def wav_seconds(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    scenes = []
    for scene in SCENES:
        aiff = AUDIO / f"{scene['id']}.aiff"
        wav = AUDIO / f"{scene['id']}.wav"
        subprocess.run(
            ["say", "-v", VOICE, "-r", str(RATE), "-o", str(aiff), scene["text"]],
            check=True,
        )
        # 48k stereo so every clip mixes without a resample step later.
        subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-i", str(aiff),
             "-ar", "48000", "-ac", "2", str(wav)],
            check=True,
        )
        aiff.unlink()
        seconds = wav_seconds(wav)
        scenes.append({**{k: v for k, v in scene.items() if k != "text"},
                       "text": scene["text"], "wav": wav.name, "seconds": seconds})
        print(f"{scene['id']:>10}  {seconds:5.1f}s")

    total = sum(s["seconds"] for s in scenes)
    print(f"{'spoken':>10}  {total:5.1f}s  ({total // 60:.0f}m{total % 60:02.0f}s)")
    (OUT / "narration.json").write_text(json.dumps(scenes, indent=2))


if __name__ == "__main__":
    main()
