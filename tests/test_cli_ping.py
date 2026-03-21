import hir.cli as cli_mod


class DummyConsole:
    def __init__(self):
        self.messages = []

    def print(self, *args, **kwargs):
        self.messages.append(" ".join(str(arg) for arg in args))

    def clear(self):
        return None

    def status(self, *args, **kwargs):
        class _Status:
            def __enter__(self_inner):
                return None

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        return _Status()


class FakePingProcess:
    def __init__(self):
        self.stdout = iter(
            [
                "64 bytes from 1.1.1.1: icmp_seq=1 ttl=58 time=10.1 ms\n",
            ]
        )
        self.terminated = False

    def terminate(self):
        self.terminated = True

    def wait(self):
        return 0


def test_cmd_ping_invalid_count_retries_without_traceback(monkeypatch):
    answers = iter(["1.1.1.1", "abc", "2", "1"])
    console = DummyConsole()
    seen = {}

    def fake_prompt(_message):
        return next(answers)

    def fake_popen(cmd, **kwargs):
        seen["cmd"] = cmd
        return FakePingProcess()

    monkeypatch.setattr(cli_mod, "prompt", fake_prompt)
    monkeypatch.setattr(cli_mod, "console", console)
    monkeypatch.setattr(cli_mod.subprocess, "Popen", fake_popen)

    cli_mod.cmd_ping()

    assert any("Entrada no válida" in message for message in console.messages)
    assert seen["cmd"] == ["ping", "-c", "2", "-W", "1", "1.1.1.1"]
