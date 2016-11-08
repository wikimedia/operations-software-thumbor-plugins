import fcntl
import logging
import os


class RotatingHandler(logging.handlers.RotatingFileHandler):
    '''This class rotates log files based on size, while supporting
    distinct python processes writing to the same file
    '''

    def doRollover(self):
        lockName = "%s.lock" % self.baseFilename
        f = open(lockName, 'a+')

        fcntl.lockf(f.fileno(), fcntl.LOCK_EX)

        filesize = os.path.getsize(self.baseFilename)

        try:
            if filesize > self.maxBytes:
                # The reference file hasn't been rotated yet, let's do it
                super(RotatingHandler, self).doRollover()
            else:
                # We are probably still be looking at the old file, close the stream
                self.close()
                if not self.delay:
                    self.stream = self._open()
        finally:
            # Unlock no matter what
            fcntl.lockf(f.fileno(), fcntl.LOCK_UN)
            f.close()
