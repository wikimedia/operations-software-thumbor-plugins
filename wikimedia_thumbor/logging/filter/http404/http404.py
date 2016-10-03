import logging


class Http404Filter(logging.Filter):
    def __init__(self, flag=None):
        self.flag = flag

    def filter(self, record):
        import re
        matches = re.match('.*HTTP 404.*', record.msg)

        if self.flag == 'exclude':
            return not matches
        elif self.flag == 'only':
            return matches

        return True
