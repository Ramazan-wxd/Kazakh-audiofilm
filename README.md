# AI Cinema

AI Cinema is a small research CLI for producing temporally aware Kazakh audio
descriptions for short, authorized videos. Milestone 1 supports a single
15–45 second input video and preserves its original runtime.

## Prerequisites

- Python 3.12 or 3.13
- An LGPL-compatible `ffmpeg` and `ffprobe` installation on `PATH`
- Gemini and Azure Speech credentials for a real cloud run

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set the required values in `.env`; it is ignored by Git.

## Run

```powershell
ai-cinema describe .\authorized-clip.mp4 --output .\described.mp4
```

The command creates local artifacts under `.ai-cinema/`. Do not commit those
artifacts: they can contain derived copyrighted media and cloud-provider output.

## Current scope

The working vertical slice probes media, transcribes dialogue, asks Gemini for
one visual event and Kazakh description, synthesizes it with Azure Speech, then
places it into a conservative speech-free window. It does not yet detect shots,
protect semantically important sound effects, process full films, or support
extended runtime.
