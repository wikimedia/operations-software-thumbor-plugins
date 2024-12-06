#!/bin/bash
# Script to inject service directory into PYTHONPATH in Docker -
# currently Blubber will set PYTHONPATH immediately before running the
# entrypoint, overriding PYTHONPATH if set via the `runs.environment`
# parameter in blubber.yaml.
# Thumbor uses importlib to import custom applications
# like ours and it will not look in the cwd, it will only obey
# PYTHONPATH.

export PYTHONPATH="/srv/service:/opt/lib/python/site-packages"
/opt/lib/venv/bin/thumbor --port 8800 --conf=thumbor.conf -a wikimedia_thumbor.app.App
