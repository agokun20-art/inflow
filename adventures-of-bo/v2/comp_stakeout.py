"""Finish 'The Stakeout': upscale, letterbox 2.39:1 in 1080p, grain, black tail, mux the mix."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_stakeout as A  # noqa: E402

FR = os.path.join(HERE, 'out', 'final')
DST = os.path.join(HERE, '..', 'output', 'v2')
os.makedirs(DST, exist_ok=True)
n = int(A.DUR * A.FPS)
missing = [f for f in range(n) if not os.path.exists(os.path.join(FR, f'f_{f:04d}.png'))]
if missing:
    sys.exit(f'{len(missing)} frames missing, first {missing[:5]}')
out = os.path.join(DST, 'Adventures_of_Bo_E01_The_Stakeout_v2_proof.mp4')
vf = ('scale=1920:804:flags=lanczos,pad=1920:1080:0:138:black,'
      'noise=c0s=3:c0f=t+u,'
      f'tpad=stop_mode=add:stop_duration={A.TAIL}:color=black,format=yuv420p')
cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(A.FPS), '-i', os.path.join(FR, 'f_%04d.png'),
       '-i', os.path.join(HERE, 'out', 'stakeout_mix.wav'), '-vf', vf, '-map', '0:v', '-map', '1:a',
       '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-tune', 'film', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
       '-shortest', '-movflags', '+faststart', '-metadata', 'title=Adventures of Bo - The Stakeout (v2 proof sequence)', out]
subprocess.run(cmd, check=True)
print(out)
