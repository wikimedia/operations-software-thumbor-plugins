#!/bin/bash
# Generate a new thumbor keyfile on run to replicate the behaviour
# previously created by the postinstall behaviour of the thumbor
# debian package.

if [ ${#} -ne 1 ] && [ ${#} -ne 2 ]; then
    echo "Usage: $0 port [other thumbor arguments]"
    echo "Example: $0 8888 \"-l debug\""
    exit 1
fi

# Made at runtime, so it exists only in the overlay upper layer. Temp names in
# the image's /tmp leave a negative dentry in each lower layer that has /tmp.
mkdir -p /tmp/thumbor && export TMPDIR=/tmp/thumbor

od --read-bytes 16 --output-duplicates --address-radix n --format x2 /dev/urandom | tr -d ' ' > /var/tmp/thumbor.key
/opt/lib/venv/bin/thumbor --port ${1} --keyfile /var/tmp/thumbor.key --conf /etc/thumbor.d/ ${2}
