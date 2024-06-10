#!/bin/bash
# Generate a new thumbor keyfile on run to replicate the behaviour
# previously created by the postinstall behaviour of the thumbor
# debian package.

if [ ${#} -ne 1 ] && [ ${#} -ne 2 ]; then
    echo "Usage: $0 port [other thumbor arguments]"
    echo "Example: $0 8888 \"-l debug\""
    exit 1
fi

export PYTHONPATH="/srv/service:/opt/lib/venv/lib/python3.11/site-packages/"
od --read-bytes 16 --output-duplicates --address-radix n --format x2 /dev/urandom | tr -d ' ' > /var/tmp/thumbor.key
/opt/lib/venv/bin/thumbor --port ${1} --keyfile /var/tmp/thumbor.key --conf /etc/thumbor.d/ ${2}
