# Twitter Download

Repository: [yuhujijijj/Twitter-Download-X-twitter](https://github.com/yuhujijijj/Twitter-Download-X-twitter)

A Python GUI and command-line tool for downloading media, text, hashtag results, replies, and profile data from Twitter/X.

> **Attribution**
>
> The overall code structure, core features, and most implementations are based on the original open-source project by [caolvchong-top](https://github.com/caolvchong-top): [twitter_download](https://github.com/caolvchong-top/twitter_download). This repository is a personally maintained and organized version with configuration-safety, GUI, packaging, and documentation updates. Please follow the original project's license and terms when using or redistributing the code.

## Features

- Batch downloads for multiple users
- Images, videos, text, reposts, highlights, and likes
- Date-range filtering and incremental synchronization
- Hashtag and advanced search downloads
- Reply and profile downloads
- CSV and Markdown output
- Tkinter GUI and Windows executable
- Optional completion sound with WAV preview and custom sound selection
- Chinese and English GUI language selection

## Quick Start

```bash
git clone https://github.com/yuhujijijj/Twitter-Download-X-twitter.git
cd Twitter-Download-X-twitter
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python gui.py
```

Copy `settings.example.json` to `settings.json`. Before the first download, click **Browse** in the GUI and select an existing download folder. The application intentionally does not fall back to the current directory.

Set the Cookie either in the GUI using separate `auth_token` and `ct0` fields, or with an environment variable:

```powershell
$env:TWITTER_COOKIE = "auth_token=...; ct0=...;"
```

Use the **Language** selector at the top of the GUI to choose Chinese or English. The selection is saved in `settings.json` and applies immediately.

## Completion Sound

Enable **Play sound when finished** in the Other Options section. The default path is `sounds`, which uses `sounds/default.wav`. Click **Preview** to test it before downloading. You can replace the default WAV file or select another WAV file with **Browse**.

## Security and Usage

- Cookies are login credentials. Never commit real cookies, logs, downloads, or personal paths.
- If a Cookie was exposed publicly, revoke the related session and obtain a new one.
- Download only content you are authorized to access and save.
- Respect Twitter/X terms of service and applicable laws.

See [TECHNOLOGY_EN.md](TECHNOLOGY_EN.md) for the architecture and configuration reference.
