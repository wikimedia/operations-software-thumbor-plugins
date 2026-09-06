#!/bin/bash
# wikimedia_thumbor is pip-installed into the image's venv, so Thumbor's
# importlib-based extension loading finds it without any PYTHONPATH juggling.

/opt/lib/venv/bin/thumbor --port 8800 --conf thumbor.conf --log-level debug --app wikimedia_thumbor.app.App
