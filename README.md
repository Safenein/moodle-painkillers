# Moodle Painkillers

[![Build and Release Python Package](https://github.com/Safenein/moodle-painkillers/actions/workflows/build_release.yml/badge.svg)](https://github.com/Safenein/moodle-painkillers/actions/workflows/build_release.yml)

A scripts to make Moodle presence status less painful.

```
I WANT TO GET PAID
```

>DISCLAIMER
>
>Use this script at your own risks. I am not responsible for whatever you do with it.
>Remember, if you are absent and set your status as present, it may involve your legal responsability.

## Overview

This repository contains a solution to authenticate yourself on Moodle and tells the administration you are present.

## Installation

To install moodle-painkillers, install it using `pip`.
This will use the latest commit on `master`.

```
pip install 'git+https://github.com/Safenein/moodle-painkillers.git'
```

Windows notifications are untested. Feel free to open issues.

MacOS users must install `terminal-notifier` for desktop notifications.
Make sure these notifications are allowed in your parameters.
You can use your system keyring to start the script.

Linux users must have `notify-send` command available.
It should be already available without further actions.

## Usage

To launch the script, make sure you provide Moodle credentials.
Here is an example of a script that would launch moodle-painkillers successfully.
Secret management using pass, "the standard unix password manager".

```bash
#!/usr/bin/env bash
export MOODLE_USERNAME="$(pass show Moodle/username)"
export MOODLE_PASSWORD="$(pass show Moodle/password)"
export DISCORD_WEBHOOK="$(pass show Discord/WebHookEmargement)"  # opt. to enable discord webhook notification

python -m moodle_painkillers
```

You can also run with CLI arguments (use --help!).

Here is a crontab example. Read disclaimer.

```
30 8 * * 1-5  /path/to/script
15 10 * * 1-5 /path/to/script
0 12 * * 1-5  /path/to/script
30 13 * * 1-5 /path/to/script
15 15 * * 1-5 /path/to/script
0 17 * * 1-5  /path/to/script
30 18 * * 1-5 /path/to/script
```

## Build

```bash
git clone https://github.com/Safenein/moodle-painkillers.git
cd moodle-painkillers

uv sync  # --no-dev pour ne pas installer les dépendances de developpement.
uv run pytest
uv build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the `GPLv3` - see the LICENSE file for details.
