# M47 MOVIE: laggy / bad-sounding opening (user report on build 46)

## Findings (stock opening.pmf vs builds 44/45/46)
| | stock | b44 | b46 | m47 main | m47 low |
|---|---|---|---|---|---|
| avg video kbps | 3701 | 3591 | 3410 | 3454 | 2203 |
| max 1 s kbps | 6372 | 5413 | 5395 | 5509 | 3559 |
| max frame bytes | 77252 | 53768 | 47976 | 48370 | 37956 |
| packs (2 KB) | 24895 | | 23701 | 24018 | 15659 |
| audio track ends | +0.43 s after video | ok | **3.2 s before video** | +0.39 s | +0.39 s |
- Profile, level, refs, B-frames, CABAC, slices (1), GOP (48) and resolution all match stock. Our peaks are LOWER than stock, so
  bitrate is not the cause.
- VUI/HRD differed (no SAR, no overscan, fixed_frame_rate 0, no pic_struct SEI, HRD 4.45 Mbps). Now matched.
- Bug: builds 45/46 copied the stock 105.1 s silent ATRAC3plus track onto a 108.3 s video, so the last 3.2 s had no audio.
  The movie thread paces/drains on its audio output (see m40/mbgm2 NOTES round 3), so this hurts the end of the movie.
  Fixed: `make47.py synth_audio` keeps the 844 stock PES byte-identical and continues the same frame stream (offsets checked).

## Most likely main cause (not fixable inside the PMF)
The song is not in the movie: the M40 hook streams ss_16 through the M22 BGM streamer (second UMD file + Atrac thread)
while sceMpeg streams the PMF. m40 QA round 3 already showed the BGM stream starving the movie's audio-output drain.
Two disc streams + two audio threads competing -> video waits on its (silent) audio clock = lag; BGM buffer underruns = bad sound.
- A/B to confirm: poke MBGM_ID = 0 (runtime 0x08D84690 → CWCheat `_L 0x20584690 0x00000000`) and play the opening.
  Smooth without the song = contention confirmed.
- Proper fix: put the song INSIDE the PMF as its ATRAC3plus track (what the stock opening does) and set MBGM_ID = 0.
  Needs an ATRAC3plus encoder (atracdenc has one, branch master/at3plus); building it was blocked by the sandbox
  permission policy in this session. Stock format: 44.1 kHz stereo, 744-byte frames (128 kbps), header 0f d0 28 5c.
- Fallback meanwhile: `opening_low.pmf` cuts the movie's disc reads ~35% below stock.

## Files
make47.py (main|low), packscan.py, manifest.json, opening_new.pmf (= main), opening_low.pmf,
out/intro47/bitrate_compare.png, chase_sample_main.mp4.

## M48: song inside the PMF (prepared; encode step blocked)
- Encoder: atracdenc (github.com/dcherednik/atracdenc, commit cb170709, libgha submodule 00a95243, LGPL-2.1), built at
  atracdenc/src/build/src/atracdenc by the coordinator with Daniel's approval. Running it from this fork was refused by the
  sandbox permission check ("Code from External"), so aud/song_pmf.at3 is NOT made yet.
- aud/song_pmf.wav (ready): disc song m22/mu/at3/ss_16.at3 decoded, +2416-sample lead-in (song t=0 = video frame 0,
  audio PTS 85069 vs video 90000), fade over the last 1.2 s of the 108.308 s video, padded to 2343 frames (108.81 s).
- build48.py: `encode` (atracdenc -e atrac3plus --container riff), then `mux`: asserts 2 ch / 44.1 kHz / 744-byte frames
  (stock 128 kbps), measures codec delay by cross-correlation and drops whole leading frames, writes frames with the stock
  8-byte header 0f d0 28 5c 00.. into the exact stock PES layout (stock PES byte positions/PTS, continuation after 105.1 s),
  muxes with v_low.h264 (2200 kbps) -> opening48.pmf, extracts the track back from the PMF, decodes it and prints
  level/peak/SNR. Dry run with the stock opening's own ATRAC3plus music as fake encoder output: round trip bit-exact.
- BOOT48M.BIN = BOOT48R (70f5c3c5) with MBGM_ID 0x580690 = 0 (1 byte), md5 86664dd50484317a039dca9fa9f6f890.
  CWCheat for the same word: _L 0x20584690 0x00000000. With MBGM_ID 0 every M40 hook is transparent, so the movie ends on
  the stock 0xff drain (the PMF now has a full-length audio track to drain).

## M48 result (2026-11-07)
- Frame size: atracdenc AT3P at 744 B loses everything above ~5 kHz (coordinator band test); 2048 B (352 kbps) matches the source.
- PPSSPP evidence (hrydgard/ppsspp bc599a1f, Core/HW/MpegDemux.cpp hasNextAudioFrame): frame size = (((code1&3)<<8)|(code2*8))+0x10
  from the 0x0FD0 header -> 0f d0 28 ff = 2056 = 8 + 2048. Private-stream sub-header: channel byte + 3 skipped bytes (offset not used).
  MediaEngine decodes PSP_CODEC_AT3PLUS with whatever frame length the demuxer returns. 352 kbps is a standard at3tool ATRAC3plus
  rate; no direct evidence that the PSP's sceMpeg hardware path accepts it in a PSMF (stock movies use 128 kbps) -> PPSSPP-first.
- opening48.pmf: 2343 frames, PPSSPP-style frame walk lands exactly on the end; codec delay 4464 samples -> 2 frames dropped,
  residual 368 samples (8 ms late); SNR vs source 30.5 dB aligned; bands 0-16 kHz within 0.1 dB, 16-20 kHz -4.8 dB;
  disc read 2598 kbps (stock 3852, b46 3585). PTS-less audio PES padded with 5 stuffing bytes so packs stay 2048.
