import logging


class ContextFilter(logging.Filter):
    port = '????'

    def __init__(self, flag=None):
        self.flag = flag

    def filter(self, record):
        import re
        # Grab the port from the very first log message and save it
        matches = re.match(
            '.*thumbor running at \d+.\d+.\d+.\d+:([\d]+).*',
            record.msg
        )

        if matches:
            type(self).port = matches.group(1)

        foo = type(self).port
        record.port = foo
        return self.flag == 'log'
