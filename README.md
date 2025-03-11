# Moodle Painkillers

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

To install moodle-painkillers, download whl file in releases and 

## Usage

To launch the script, make sure you provide Moodle credentials.

```bash
export MOODLE_USERNAME="$(pass show Moodle/username)"
export MOODLE_PASSWORD="$(pass show Moodle/password)"
export DISCORD_WEBHOOK="$(pass show Discord/WebHookEmargement)"  # opt. to enable discord webhook notification

python -m moodle_painkillers
```

## Build

```bash
git clone https://github.com/username/moodle-painkillers.git
cd moodle-painkillers

uv sync
uv run pytest --cov
uv build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the `GPLv3` - see the LICENSE file for details.