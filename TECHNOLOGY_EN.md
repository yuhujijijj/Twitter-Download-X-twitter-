# Twitter Download Technical Notes

## Stack

- Python 3.8+
- Tkinter for the desktop GUI
- `httpx` for HTTP requests and media downloads
- `requests`, `beautifulsoup4`, and `XClientTransaction` for transaction ID generation
- JSON configuration, CSV/Markdown output, and pickle-based cache files

## Main Modules

| Module | Responsibility |
|---|---|
| `main.py` | Main user media download flow |
| `gui.py` | Chinese/English GUI, configuration, download and sync controls |
| `common.py` | Settings, headers, proxy, request throttling and shared helpers |
| `sync_manager.py` | Scan local users and update selected users |
| `text_down.py` | Text-only tweet export |
| `tag_down.py` | Hashtag and advanced-search downloads |
| `reply_down.py` | Reply and conversation downloads |
| `profile_down.py` | Avatar, banner and profile description downloads |
| `csv_gen.py` / `md_gen.py` | CSV and Markdown generation |
| `cache_gen.py` | Download and user cache management |

## GUI Language

The GUI supports Chinese (`zh-CN`) and English (`en-US`). Choose the language from the selector at the top of the window. The choice is saved in `settings.json` and is applied immediately to labels, buttons, tabs, and table headings.

## Completion Sound

The GUI supports optional completion sounds on Windows. Set `completion_sound` to `true` to enable playback. `completion_sound_path` defaults to `sounds`; this resolves to `sounds/default.wav`. The **Preview** button plays the selected sound without starting a download. Custom WAV files can be selected from the GUI.

The download page uses a resizable Canvas with mouse-wheel forwarding for child controls, so all settings remain accessible in small-window mode. `save_path` must be an existing folder selected by the user; the application does not fall back to the current directory.

## Configuration

| Key | Type | Description |
|---|---|---|
| `save_path` | string | Required existing download directory |
| `user_lst` | string | Comma-separated usernames |
| `cookie` | string | Cookie containing `auth_token` and `ct0` |
| `language` | string | `zh-CN` or `en-US` |
| `completion_sound` | boolean | Enable completion sound |
| `completion_sound_path` | string | Sound directory or WAV file path |
| `max_concurrent_requests` | integer | Maximum concurrent requests |
| `request_interval` | number | Delay between API requests in seconds |
| `proxy` | string | Optional proxy URL |
| `image_format` | string | `orig`, `jpg`, or `png` |

The complete sample configuration is available in `settings.example.json`.
