"""Cut the raw capture down to the narration and lay the voice over it.

Three passes, because doing it in one is where the drift comes from:

  1. Normalise raw.webm to constant-rate h264. Playwright writes a variable
     frame rate file, and `setpts` on VFR footage slides out of sync.
  2. Per scene, trim the capture and speed the body up until it fits the
     sentence spoken over it, leaving any `hold` tail at natural speed. This is
     what removes the dead air spent watching the typing indicator.
  3. Mix the narration clips at their scene offsets and mux.

Output: docs/demo/readyhome-demo.mp4
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUT = Path(__file__).resolve().parents[1] / "docs" / "demo"
AUDIO = OUT / "audio"
LEAD = 0.45   # let the picture settle before the voice comes in
PAD = 1.0     # must match record_demo.PAD
FPS = 30


def run(args):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], check=True)


def duration(path: Path) -> float:
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def main() -> None:
    scenes = json.loads((OUT / "scenes.json").read_text())
    raw, norm = OUT / "raw.webm", OUT / "norm.mp4"

    # Scene marks carry the narration lengths as they were at record time. Trust
    # the wav files instead, so a reworded line can be re-timed without paying
    # for another live run -- the recorder only ever waited too long, never too
    # little, and a scene that overruns its line just holds a moment longer.
    spoken = {s["id"]: s["seconds"]
              for s in json.loads((OUT / "narration.json").read_text())}
    for sc in scenes:
        sc["narration"] = spoken[sc["id"]]

    print("1/3  normalising the capture ...", flush=True)
    run(["-i", str(raw), "-vf", f"fps={FPS}", "-c:v", "libx264", "-crf", "20",
         "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", str(norm)])

    wall = scenes[-1]["end"]
    vid = duration(norm)
    # The capture should run on the same clock the recorder stamped its marks
    # against. If it does not, every cut below is off by a growing amount, so
    # rescale rather than silently drift.
    scale = vid / wall if wall else 1.0
    print(f"     capture {vid:.1f}s vs wall clock {wall:.1f}s  (drift {scale:.4f}x)")
    if abs(scale - 1) > 0.02:
        print("     -> rescaling scene marks onto the video clock")
    else:
        scale = 1.0

    print("2/3  fitting each scene to its narration ...", flush=True)
    parts, filters, offsets, cursor = [], [], {}, 0.0
    for sc in scenes:
        start, end = sc["start"] * scale, sc["end"] * scale
        target = sc["narration"] + PAD
        hold = min(sc["hold"], max(end - start - 0.5, 0.0))
        body = (end - start) - hold
        want_body = max(target - hold, 0.3)
        speed = min(max(body / want_body, 1.0), sc["max_speed"])

        offsets[sc["id"]] = cursor
        i = len(parts)
        filters.append(f"[0:v]trim={start:.3f}:{start + body:.3f},"
                       f"setpts=(PTS-STARTPTS)/{speed:.5f}[v{i}]")
        parts.append(f"[v{i}]")
        cursor += body / speed
        if hold > 0.05:
            j = len(parts)
            filters.append(f"[0:v]trim={start + body:.3f}:{end:.3f},"
                           f"setpts=PTS-STARTPTS[v{j}]")
            parts.append(f"[v{j}]")
            cursor += hold
        if sc["narration"] + LEAD > cursor - offsets[sc["id"]] + 1e-6:
            over = sc["narration"] + LEAD - (cursor - offsets[sc["id"]])
            print(f"     !! {sc['id']}: narration overruns its footage by "
                  f"{over:.1f}s and will talk over the next scene. Shorten the "
                  f"line, or give the scene more to show.")
        print(f"     {sc['id']:>10}  {end - start:5.1f}s real -> "
              f"{cursor - offsets[sc['id']]:5.1f}s  (x{speed:.2f}"
              f"{', hold ' + format(hold, '.1f') + 's' if hold > 0.05 else ''})")

    filters.append("".join(parts) + f"concat=n={len(parts)}:v=1:a=0[vout]")
    cut = OUT / "cut.mp4"
    run(["-i", str(norm), "-filter_complex", ";".join(filters), "-map", "[vout]",
         "-c:v", "libx264", "-crf", "20", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-r", str(FPS), str(cut)])
    total = duration(cut)
    print(f"     edited length: {total:.1f}s ({total // 60:.0f}m{total % 60:02.0f}s)")

    print("3/3  mixing the voice track ...", flush=True)
    ins, mix, labels = [], [], []
    for n, sc in enumerate(scenes):
        ins += ["-i", str(AUDIO / f"{sc['id']}.wav")]
        ms = int((offsets[sc["id"]] + LEAD) * 1000)
        mix.append(f"[{n}:a]adelay={ms}|{ms}[a{n}]")
        labels.append(f"[a{n}]")
    # normalize=0 keeps each clip at its recorded level (they never overlap);
    # the limiter catches the peaks the small lift would otherwise clip.
    mix.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:"
                                 f"duration=longest,volume=1.3,"
                                 f"alimiter=limit=0.95[aout]")
    voice = OUT / "voice.wav"
    run([*ins, "-filter_complex", ";".join(mix), "-map", "[aout]",
         "-ar", "48000", "-ac", "2", str(voice)])

    final = OUT / "readyhome-demo.mp4"
    run(["-i", str(cut), "-i", str(voice), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", str(final)])

    for tmp in (norm, cut, voice):
        tmp.unlink(missing_ok=True)
    d = duration(final)
    print(f"\n{final}")
    print(f"  {d // 60:.0f}m{d % 60:02.0f}s   {final.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
