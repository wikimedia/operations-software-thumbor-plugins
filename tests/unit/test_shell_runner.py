from types import SimpleNamespace

from wikimedia_thumbor.shell_runner import ShellRunner


def context(**config):
    return SimpleNamespace(config=SimpleNamespace(**config))


class TestWrapCommand:
    def test_returns_command_untouched_when_timeouts_are_off(self):
        ctx = context(SUBPROCESS_USE_TIMEOUT=False)
        command = ["/usr/bin/vips", "copy"]

        assert ShellRunner.wrap_command(command, ctx) == command

    def test_returns_command_untouched_when_setting_is_absent(self):
        assert ShellRunner.wrap_command(["/usr/bin/vips"], context()) == ["/usr/bin/vips"]

    def test_wraps_command_in_timeout(self):
        ctx = context(
            SUBPROCESS_USE_TIMEOUT=True,
            SUBPROCESS_TIMEOUT=60,
            SUBPROCESS_TIMEOUT_PATH="/usr/bin/timeout",
        )

        assert ShellRunner.wrap_command(["/usr/bin/vips", "copy"], ctx) == [
            "/usr/bin/timeout",
            "--foreground",
            "60",
            "/usr/bin/vips",
            "copy",
        ]

    def test_kill_after_is_inserted_before_the_duration(self):
        ctx = context(
            SUBPROCESS_USE_TIMEOUT=True,
            SUBPROCESS_TIMEOUT=60,
            SUBPROCESS_TIMEOUT_PATH="/usr/bin/timeout",
            SUBPROCESS_TIMEOUT_KILL_AFTER=5,
        )

        assert ShellRunner.wrap_command(["/usr/bin/vips"], ctx) == [
            "/usr/bin/timeout",
            "--foreground",
            "--kill-after",
            "5s",
            "60",
            "/usr/bin/vips",
        ]

    def test_kill_after_of_zero_is_omitted(self):
        ctx = context(
            SUBPROCESS_USE_TIMEOUT=True,
            SUBPROCESS_TIMEOUT=60,
            SUBPROCESS_TIMEOUT_PATH="/usr/bin/timeout",
            SUBPROCESS_TIMEOUT_KILL_AFTER=0,
        )

        assert "--kill-after" not in ShellRunner.wrap_command(["/usr/bin/vips"], ctx)
