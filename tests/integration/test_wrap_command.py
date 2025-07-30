from . import WikimediaTestCase
from wikimedia_thumbor.shell_runner import ShellRunner


class WikimediaShellRunnerWrapCommandTest(WikimediaTestCase):
    def test_wrap_command_with_timeout_and_kill_after(self):
        self.ctx.config.SUBPROCESS_USE_TIMEOUT = True
        self.ctx.config.SUBPROCESS_TIMEOUT = 60
        self.ctx.config.SUBPROCESS_TIMEOUT_PATH = "/usr/bin/timeout"
        self.ctx.config.SUBPROCESS_TIMEOUT_KILL_AFTER = 5

        command = ["echo", "hello"]

        result = ShellRunner.wrap_command(command, self.ctx)

        expected = [
            "/usr/bin/timeout", "--foreground",
            "--kill-after", "5s", "60", "echo", "hello"
        ]

        assert result == expected

    def test_wrap_command_with_timeout_without_kill_after(self):
        self.ctx.config.SUBPROCESS_USE_TIMEOUT = True
        self.ctx.config.SUBPROCESS_TIMEOUT = 30
        self.ctx.config.SUBPROCESS_TIMEOUT_PATH = "/usr/bin/timeout"
        self.ctx.config.SUBPROCESS_TIMEOUT_KILL_AFTER = 0

        command = ["echo", "world"]

        result = ShellRunner.wrap_command(command, self.ctx)

        expected = [
            "/usr/bin/timeout", "--foreground", "30", "echo", "world"
        ]

        assert result == expected

    def test_wrap_command_without_timeout(self):
        self.ctx.config.SUBPROCESS_USE_TIMEOUT = False
        command = ["echo", "no-timeout"]

        result = ShellRunner.wrap_command(command, self.ctx)

        assert result == command
