#!/bin/bash
set -euo pipefail

cmd.exe /c pytest -q
node --check logcheck/web_static/app.js
