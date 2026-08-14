import argparse
import base64
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

import yaml
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent

loader = importlib.machinery.SourceFileLoader("agent_run", str(ROOT / "bin" / "agent-run"))
spec = importlib.util.spec_from_loader("agent_run", loader)
agent_run = importlib.util.module_from_spec(spec)
loader.exec_module(agent_run)

# Compiler tests use a fixture, so evolving a real template cannot break them.
TEMPLATE = ROOT / "tests" / "fixtures" / "example.yaml"


def write_yaml(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    f.write(content)
    f.close()
    return f.name


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def status_args(**overrides):
    defaults = dict(offline=False, json=False)
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def logs_args(name, **overrides):
    defaults = dict(name=name, lines=40, source="auto", follow=False)
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def run_args(name, **overrides):
    defaults = dict(name=name, prompt_file=None, sandbox="workspace-write", force=False)
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class ValidateTests(unittest.TestCase):
    def test_example_template_is_valid(self):
        template = agent_run.load_template(TEMPLATE)
        self.assertEqual(template["name"], "example-app")

    def test_missing_runtimes_rejected(self):
        path = write_yaml(
            "version: 1\nname: broken\nrepos:\n  - id: github.com/a/b\n"
        )
        with self.assertRaises(agent_run.TemplateError):
            agent_run.load_template(path)

    def test_provider_api_keys_rejected(self):
        path = write_yaml(
            "version: 1\nname: sneaky\nruntimes: [codex]\n"
            "repos:\n  - id: github.com/a/b\n"
            "env:\n  OPENAI_API_KEY: nope\n"
        )
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.load_template(path)
        self.assertIn("OPENAI_API_KEY", str(ctx.exception))


class CompileTests(unittest.TestCase):
    def compile(self, runtime="codex"):
        template = agent_run.load_template(TEMPLATE)
        return agent_run.compile_exe_dev(template, runtime, f"example-app-{runtime}")

    def test_command_carries_template_settings(self):
        argv, _ = self.compile()
        command = agent_run.display_command(argv, "setup.sh")
        for expected in [
            "ssh exe.dev new --json",
            "--name=example-app-codex",
            "--cpu=4",
            "--memory=8GB",
            "--disk=50GB",
            "--image=exeuntu",
            "--env=NODE_ENV=development",
            "--integration=github",
            "--tag=agent-pilot",
            "--comment=agent-run:example-app:codex",
            "--setup-script=/dev/stdin",
            "< setup.sh",
        ]:
            self.assertIn(expected, command)

    def test_setup_script_contents(self):
        _, script = self.compile()
        self.assertIn(
            'git clone --branch main https://github.int.exe.xyz/lightdash/lightdash.git "$WORK"/lightdash',
            script,
        )
        self.assertIn("sudo exeuntu update codex", script)
        self.assertNotIn("update claude", script)
        self.assertIn('( cd "$WORK"/lightdash && corepack enable && pnpm install )', script)
        self.assertIn(".agent-run-ready", script)
        self.assertLessEqual(len(script.encode()), agent_run.SETUP_SCRIPT_LIMIT)

    def test_claude_runtime_swaps_only_runtime_bits(self):
        argv, script = self.compile("claude")
        self.assertIn("--comment=agent-run:example-app:claude", argv)
        self.assertIn("sudo exeuntu update claude", script)
        self.assertNotIn("update codex", script)

    def test_disallowed_runtime_rejected(self):
        template = agent_run.load_template(TEMPLATE)
        template["runtimes"] = ["codex"]
        with self.assertRaises(agent_run.TemplateError):
            agent_run.compile_exe_dev(template, "claude", "x")

    def test_whitespace_in_remote_arguments_rejected(self):
        # ssh joins remote args with spaces; exe.dev's parser has no quoting.
        template = agent_run.load_template(TEMPLATE)
        template["env"] = {"GREETING": "hello world"}
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.compile_exe_dev(template, "codex", "x")
        self.assertIn("split by the provider's parser", str(ctx.exception))

    def test_clone_url_follows_repo_intent_not_integration_name(self):
        # The gateway hostname is aggregate, so recognising an integration by
        # name is wrong: a github integration may be called anything.
        template = agent_run.load_template(TEMPLATE)
        template["providers"]["exe.dev"]["integrations"] = ["some-repo-integration"]
        template["repos"][0]["private"] = False
        _, script = agent_run.compile_exe_dev(template, "codex", "x")
        self.assertIn("https://github.com/lightdash/lightdash.git", script)

        template["repos"][0]["private"] = True
        _, script = agent_run.compile_exe_dev(template, "codex", "x")
        self.assertIn("https://github.int.exe.xyz/lightdash/lightdash.git", script)


class ProviderErrorTests(unittest.TestCase):
    def test_sh_error_includes_stdout(self):
        # exe.dev reports errors as JSON on stdout with an empty stderr.
        fake = completed(returncode=1, stdout='{"error":"--tag not allowed"}')
        with mock.patch.object(agent_run.subprocess, "run", return_value=fake):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.sh(["ssh", "exe.dev", "new"])
        self.assertIn("--tag not allowed", str(ctx.exception))

    def test_create_vm_surfaces_error_field(self):
        fake = completed(stdout='{"error":"quota exceeded"}')
        with mock.patch.object(agent_run, "sh", return_value=fake):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.create_vm(["ssh", "exe.dev", "new"], "script")
        self.assertIn("quota exceeded", str(ctx.exception))


class RunStateTestCase(unittest.TestCase):
    """Base class giving each test an isolated state root."""

    def setUp(self):
        self.state_dir = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"AGENT_RUN_STATE_PATH": self.state_dir.name})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.state_dir.cleanup)


class DispatchTests(RunStateTestCase):
    def dispatch_args(self, **overrides):
        defaults = dict(
            template=str(TEMPLATE),
            provider="exe.dev",
            runtime="codex",
            name="task-a",
            prompt_file=None,
            no_wait=False,
            wait_timeout=60,
            poll_interval=1,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_dispatch_creates_record_and_waits_for_ready(self):
        responses = [
            completed(stdout=json.dumps({"vm_name": "task-a", "ssh_dest": "u123@task-a.exe.xyz"})),
            completed(returncode=1, stderr="No such file"),
            completed(stdout="2026-08-10T20:00:00Z\n"),
        ]
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(args)
            return responses.pop(0)

        with mock.patch.object(agent_run, "sh", fake_sh), mock.patch.object(agent_run.time, "sleep"):
            agent_run.cmd_dispatch(self.dispatch_args())

        self.assertEqual(calls[0][:4], ["ssh", "exe.dev", "new", "--json"])
        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["vm"], "task-a")
        self.assertEqual(record["status"], "ready")
        self.assertEqual(record["ssh_dest"], "u123@task-a.exe.xyz")
        self.assertEqual(record["ready_at"], "2026-08-10T20:00:00Z")

    def test_dispatch_pushes_prompt_file_base64_via_gateway(self):
        prompt = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        prompt.write("do the thing")
        prompt.close()
        responses = [
            completed(stdout=json.dumps({"vm_name": "task-a", "ssh_dest": "u@vm"})),
            completed(stdout="2026-08-10T20:00:00Z\n"),
            completed(),
        ]
        pushed = {}

        def fake_sh(args, input_text=None, check=True):
            command = args[-1]
            if "base64 -d > ~/work/TASK.md" in command:
                # the gateway drops stdin, so content must ride in the command
                self.assertIsNone(input_text)
                self.assertEqual(args[-2], "task-a")  # exec targets the VM name
                encoded = command.split("echo ")[1].split()[0]
                pushed["content"] = base64.b64decode(encoded).decode()
            return responses.pop(0)

        with mock.patch.object(agent_run, "sh", fake_sh):
            agent_run.cmd_dispatch(self.dispatch_args(prompt_file=prompt.name))

        self.assertEqual(pushed["content"], "do the thing")

    def test_vm_exec_routes_through_gateway(self):
        with mock.patch.object(agent_run, "sh", return_value=completed()) as fake:
            agent_run.vm_exec("task-a", "cat ~/work/.agent-run-ready", check=False)
        args = fake.call_args.args[0]
        self.assertEqual(args[-4:], ["exe.dev", "ssh", "task-a", "cat ~/work/.agent-run-ready"])

    # The gateway exits 0 even when the inner command fails, and folds the
    # inner stderr into stdout. Observed verbatim in two real run records,
    # where it was stored as the readiness timestamp and the VM was declared
    # ready before its setup had finished.
    GATEWAY_CAT_ERROR = "cat: /home/exedev/work/.agent-run-ready: No such file or directory\n"

    def test_wait_ready_rejects_gateway_error_text(self):
        responses = [
            completed(stdout=json.dumps({"vm_name": "task-a", "ssh_dest": "u@vm"})),
            completed(stdout=self.GATEWAY_CAT_ERROR),
            completed(stdout=self.GATEWAY_CAT_ERROR),
            completed(stdout="2026-08-11T00:29:16Z\n"),
        ]

        def fake_sh(args, input_text=None, check=True):
            return responses.pop(0)

        with mock.patch.object(agent_run, "sh", fake_sh), mock.patch.object(agent_run.time, "sleep"):
            agent_run.cmd_dispatch(self.dispatch_args())

        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["ready_at"], "2026-08-11T00:29:16Z")
        self.assertEqual(responses, [])  # kept polling instead of accepting the error

    def test_wait_ready_times_out_when_marker_never_appears(self):
        responses = [completed(stdout=json.dumps({"vm_name": "task-a", "ssh_dest": "u@vm"}))]

        def fake_sh(args, input_text=None, check=True):
            if responses:
                return responses.pop(0)
            return completed(stdout=self.GATEWAY_CAT_ERROR)

        with mock.patch.object(agent_run, "sh", fake_sh), mock.patch.object(agent_run.time, "sleep"):
            with self.assertRaises(agent_run.RunError):
                agent_run.cmd_dispatch(self.dispatch_args(wait_timeout=0))

        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["status"], "provisioning")
        self.assertNotIn("ready_at", record)

    def test_dispatch_refuses_duplicate_run_name(self):
        agent_run.save_run({"name": "task-a", "status": "ready", "created_at": "x"})
        with self.assertRaises(agent_run.RunError):
            agent_run.cmd_dispatch(self.dispatch_args())

    def test_dispatch_no_wait_skips_polling(self):
        responses = [completed(stdout=json.dumps({"name": "task-a", "ssh_dest": "u@vm"}))]

        def fake_sh(args, input_text=None, check=True):
            return responses.pop(0)

        with mock.patch.object(agent_run, "sh", fake_sh):
            agent_run.cmd_dispatch(self.dispatch_args(no_wait=True))

        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["status"], "provisioning")


class StatusAndRmTests(RunStateTestCase):
    def seed_run(self, name="task-a", status="ready"):
        agent_run.save_run(
            {
                "name": name,
                "vm": name,
                "ssh_dest": "u@vm",
                "provider": "exe.dev",
                "template": "t.yaml",
                "runtime": "codex",
                "status": status,
                "created_at": "2026-08-10T19:00:00Z",
            }
        )

    def test_status_flags_missing_vms(self):
        self.seed_run()
        listing = completed(stdout=json.dumps({"vms": [{"vm_name": "some-other-vm"}]}))
        with mock.patch.object(agent_run, "sh", lambda *a, **k: listing):
            with mock.patch("builtins.print") as fake_print:
                agent_run.cmd_status(status_args())
        output = "\n".join(str(c.args[0]) for c in fake_print.call_args_list if c.args)
        self.assertIn("missing", output)

    def test_status_promotes_provisioning_run_when_marker_exists(self):
        self.seed_run(status="provisioning")
        responses = [
            completed(stdout=json.dumps({"vms": [{"vm_name": "task-a"}]})),  # provider ls
            completed(stdout="2026-08-11T00:15:00Z\n"),  # marker probe
        ]

        def fake_sh(args, input_text=None, check=True):
            return responses.pop(0)

        with mock.patch.object(agent_run, "sh", fake_sh):
            with mock.patch("builtins.print"):
                agent_run.cmd_status(status_args())

        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["status"], "ready")
        self.assertEqual(record["ready_at"], "2026-08-11T00:15:00Z")

    def test_status_keeps_provisioning_when_probe_returns_gateway_error(self):
        self.seed_run(status="provisioning")
        responses = [
            completed(stdout=json.dumps({"vms": [{"vm_name": "task-a"}]})),  # provider ls
            completed(stdout="cat: /home/exedev/work/.agent-run-ready: No such file or directory\n"),
        ]

        def fake_sh(args, input_text=None, check=True):
            return responses.pop(0)

        with mock.patch.object(agent_run, "sh", fake_sh):
            with mock.patch("builtins.print"):
                agent_run.cmd_status(status_args())

        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["status"], "provisioning")
        self.assertNotIn("ready_at", record)

    def test_logs_shows_setup_journal_tail(self):
        self.seed_run()
        log = completed(stdout="line1\nline2\nline3\n")
        with mock.patch.object(agent_run, "sh", return_value=log):
            with mock.patch("builtins.print") as fake_print:
                agent_run.cmd_logs(logs_args("task-a", lines=2, source="setup"))
        self.assertEqual(fake_print.call_args.args[0], "line2\nline3")

    def test_rm_deletes_vm_and_marks_record(self):
        self.seed_run()
        responses = [
            completed(stdout=json.dumps([{"name": "task-a"}])),
            completed(),
        ]

        def fake_sh(args, input_text=None, check=True):
            return responses.pop(0)

        with mock.patch.object(agent_run, "sh", fake_sh):
            agent_run.cmd_rm(argparse.Namespace(name="task-a", yes=True))

        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["status"], "deleted")

    def test_rm_marks_already_gone_vm_without_provider_call(self):
        self.seed_run()
        listing = completed(stdout=json.dumps([]))
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(args)
            return listing

        with mock.patch.object(agent_run, "sh", fake_sh):
            agent_run.cmd_rm(argparse.Namespace(name="task-a", yes=True))

        self.assertEqual(len(calls), 1)  # only the listing; no 'rm'
        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["status"], "deleted")

    def test_rm_unknown_run_rejected(self):
        with self.assertRaises(agent_run.RunError):
            agent_run.cmd_rm(argparse.Namespace(name="nope", yes=True))


if __name__ == "__main__":
    unittest.main()


class RunnerTests(unittest.TestCase):
    def test_runner_carries_sandbox_and_captures_exit_code(self):
        script = agent_run.render_runner("codex", "danger-full-access", "~/work/repo")
        self.assertIn("--sandbox danger-full-access", script)
        self.assertIn('cd "$WORKDIR"', script)
        # tmux's session lifetime is the agent's, so the runner must not background.
        self.assertNotIn("&", script.replace("2>&1", "").replace("&&", ""))
        self.assertIn("rc=${PIPESTATUS[0]}", script)
        self.assertIn(agent_run.shell_path(agent_run.AGENT_EXIT_REMOTE), script)

    def test_runner_reads_the_prompt_from_a_file(self):
        # Model-facing text must never be interpolated into a gateway command.
        script = agent_run.render_runner("codex", "workspace-write", "~/work/repo")
        self.assertIn(f"$(cat {agent_run.shell_path(agent_run.PROMPT_REMOTE)})", script)

    def test_unknown_sandbox_rejected(self):
        with self.assertRaises(agent_run.RunError):
            agent_run.render_runner("codex", "wide-open", "~/work")

    def test_unknown_runtime_rejected(self):
        with self.assertRaises(agent_run.RunError):
            agent_run.render_runner("gopher", "workspace-write", "~/work")

    def test_primary_workdir_prefers_the_primary_repo(self):
        template = {
            "repos": [
                {"id": "github.com/o/tools", "path": "tools", "role": "support"},
                {"id": "github.com/o/app", "role": "primary"},
            ]
        }
        self.assertEqual(agent_run.primary_workdir(template), "~/work/app")

    def test_primary_workdir_without_repos(self):
        self.assertEqual(agent_run.primary_workdir({"repos": []}), "~/work")


class AgentStateTests(unittest.TestCase):
    def test_parses_running_and_exit_codes(self):
        self.assertEqual(agent_run.parse_agent_state("RUNNING\n"), "running")
        self.assertEqual(agent_run.parse_agent_state("DONE:0\n"), "exited(0)")
        self.assertEqual(agent_run.parse_agent_state("DONE:2\n"), "exited(2)")

    def test_unknown_exit_code_is_still_reported_as_exited(self):
        self.assertEqual(agent_run.parse_agent_state("DONE:?\n"), "exited(?)")

    def test_unreadable_probe_is_not_mistaken_for_a_state(self):
        # The gateway folds stderr into stdout and exits 0; junk must not parse.
        self.assertIsNone(agent_run.parse_agent_state("bash: tmux: command not found\n"))
        self.assertIsNone(agent_run.parse_agent_state(""))

    def test_probe_command_is_whitespace_quoting_free(self):
        self.assertNotIn('"', agent_run.AGENT_STATE_CMD)
        self.assertNotIn("'", agent_run.AGENT_STATE_CMD)


class ObserveTests(RunStateTestCase):
    def seed(self, name="task-a", **extra):
        record = {
            "name": name,
            "vm": name,
            "ssh_dest": "u@vm",
            "provider": "exe.dev",
            "template": "t.yaml",
            "runtime": "codex",
            "status": "ready",
            "created_at": "2026-08-14T05:00:00Z",
            "workdir": "~/work/dot-files",
        }
        record.update(extra)
        agent_run.save_run(record)
        return record

    def test_run_starts_a_detached_tmux_session_and_records_it(self):
        self.seed()
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(args[-1])
            return completed(stdout="DONE:0\n")

        with mock.patch.object(agent_run, "sh", fake_sh):
            agent_run.cmd_run(run_args("task-a", sandbox="danger-full-access"))

        self.assertTrue(any("tmux new-session -d -s agent" in c for c in calls))
        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["tmux_session"], "agent")
        self.assertEqual(record["sandbox"], "danger-full-access")
        self.assertTrue(record["started_at"])

    def test_run_refuses_a_vm_that_is_not_ready(self):
        self.seed(status="provisioning")
        with self.assertRaises(agent_run.RunError) as ctx:
            agent_run.cmd_run(run_args("task-a"))
        self.assertIn("not ready", str(ctx.exception))

    def test_run_refuses_to_double_start_without_force(self):
        self.seed(started_at="2026-08-14T05:01:00Z")
        with mock.patch.object(agent_run, "sh", lambda *a, **k: completed(stdout="RUNNING\n")):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.cmd_run(run_args("task-a"))
        self.assertIn("already running", str(ctx.exception))

    def test_attach_refuses_when_no_agent_is_live(self):
        self.seed(started_at="2026-08-14T05:01:00Z")
        with mock.patch.object(agent_run, "sh", lambda *a, **k: completed(stdout="DONE:0\n")):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.cmd_attach(argparse.Namespace(name="task-a"))
        self.assertIn("no live agent", str(ctx.exception))

    def test_attach_and_follow_route_through_the_gateway(self):
        self.assertEqual(
            agent_run.attach_argv("task-a"),
            ["ssh", "-t", "exe.dev", "ssh", "task-a", "tmux", "attach", "-t", "agent"],
        )
        self.assertEqual(
            agent_run.follow_argv("task-a", "~/work/agent.log"),
            ["ssh", "exe.dev", "ssh", "task-a", "tail", "-n", "200", "-f", "~/work/agent.log"],
        )

    def test_logs_defaults_to_setup_before_the_agent_starts(self):
        self.seed()
        seen = []

        def fake_sh(args, input_text=None, check=True):
            seen.append(args[-1])
            return completed(stdout="boot line\n")

        with mock.patch.object(agent_run, "sh", fake_sh), mock.patch("builtins.print"):
            agent_run.cmd_logs(logs_args("task-a"))
        self.assertIn(agent_run.SETUP_LOG_CMD, seen)

    def test_logs_defaults_to_the_agent_once_started(self):
        self.seed(started_at="2026-08-14T05:01:00Z", agent_log="~/work/agent.log")
        seen = []

        def fake_sh(args, input_text=None, check=True):
            seen.append(args[-1])
            return completed(stdout="agent line\n")

        with mock.patch.object(agent_run, "sh", fake_sh), mock.patch("builtins.print"):
            agent_run.cmd_logs(logs_args("task-a"))
        self.assertTrue(any("tail -n 40 ~/work/agent.log" in c for c in seen))

    def test_status_json_reports_agent_state(self):
        self.seed(started_at="2026-08-14T05:01:00Z")
        responses = [
            completed(stdout=json.dumps({"vms": [{"vm_name": "task-a"}]})),
            completed(stdout="RUNNING\n"),
        ]
        printed = []
        with mock.patch.object(agent_run, "sh", lambda *a, **k: responses.pop(0)):
            with mock.patch("builtins.print", lambda *a, **k: printed.append(a[0] if a else "")):
                agent_run.cmd_status(status_args(json=True))
        payload = json.loads(printed[-1])
        self.assertEqual(payload["runs"][0]["agent"], "running")
        self.assertEqual(payload["runs"][0]["vm_status"], "ready")


class MonitorPlanTests(unittest.TestCase):
    def test_opens_new_windows_and_prunes_gone_ones(self):
        add, kill = agent_run.plan_monitor_windows(["a", "b"], ["b", "c"])
        self.assertEqual((add, kill), (["c"], ["a"]))

    def test_untouched_when_nothing_changed(self):
        # Refreshing must not disturb the window you are watching.
        self.assertEqual(agent_run.plan_monitor_windows(["a", "b"], ["a", "b"]), ([], []))


class ShellPathTests(unittest.TestCase):
    def test_tilde_becomes_home_so_it_survives_quoting(self):
        # Bash expands a bare ~ but not a quoted one; every path here is quoted.
        self.assertEqual(agent_run.shell_path("~/work/repo"), "$HOME/work/repo")
        self.assertEqual(agent_run.shell_path("~"), "$HOME")

    def test_absolute_and_relative_paths_are_untouched(self):
        self.assertEqual(agent_run.shell_path("/srv/repo"), "/srv/repo")
        self.assertEqual(agent_run.shell_path("work/repo"), "work/repo")

    def test_runner_never_quotes_a_bare_tilde(self):
        # The regression: WORKDIR="~/work/x" made cd fail and killed the session.
        script = agent_run.render_runner("codex", "workspace-write", "~/work/repo")
        self.assertNotIn('"~', script)
        self.assertIn('WORKDIR="$HOME/work/repo"', script)


class MonitorPreconditionTests(RunStateTestCase):
    def test_monitor_explains_how_to_get_tmux_and_what_works_without_it(self):
        with mock.patch.object(agent_run.shutil, "which", return_value=None):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.cmd_monitor(argparse.Namespace(session="s"))
        message = str(ctx.exception)
        self.assertIn("brew install tmux", message)
        self.assertIn("attach", message)  # the path that needs no local tmux


class SandboxAcrossRuntimesTests(unittest.TestCase):
    def test_every_sandbox_mode_reaches_the_claude_command_line(self):
        # A flag that silently does nothing is worse than no flag.
        for mode, expected in [
            ("read-only", "plan"),
            ("workspace-write", "acceptEdits"),
            ("danger-full-access", "bypassPermissions"),
        ]:
            script = agent_run.render_runner("claude", mode, "~/work/repo")
            self.assertIn(f"--permission-mode {expected}", script)

    def test_every_sandbox_mode_reaches_the_codex_command_line(self):
        for mode in agent_run.SANDBOX_MODES:
            script = agent_run.render_runner("codex", mode, "~/work/repo")
            self.assertIn(f"--sandbox {mode}", script)

    def test_both_runtimes_cover_every_declared_mode(self):
        self.assertEqual(set(agent_run.CLAUDE_PERMISSION_MODE), set(agent_run.SANDBOX_MODES))


class MonitorSessionTests(RunStateTestCase):
    def test_new_dashboard_keeps_windows_after_their_stream_ends(self):
        # Without remain-on-exit the last finished window closes the session,
        # taking the whole dashboard with it.
        agent_run.save_run(
            {"name": "a", "vm": "a", "runtime": "codex", "status": "ready",
             "created_at": "2026-08-14T05:00:00Z"}
        )
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(args)
            # has-session fails -> the session must be created
            return completed(returncode=1) if args[1] == "has-session" else completed()

        with mock.patch.object(agent_run.shutil, "which", return_value="/usr/bin/tmux"):
            with mock.patch.object(agent_run, "sh", fake_sh), mock.patch("builtins.print"):
                agent_run.cmd_monitor(argparse.Namespace(session="dash"))

        self.assertTrue(
            any(a[:2] == ["tmux", "set-option"] and "remain-on-exit" in a for a in calls),
            "dashboard session must set remain-on-exit",
        )


class ConfigureStepTests(unittest.TestCase):
    def test_configure_step_renders_discovery_for_each_runtime(self):
        template = {
            "name": "t", "runtimes": ["codex", "claude"],
            "repos": [{"id": "github.com/o/r"}],
            "setup": ["configure-llm-integration"],
        }
        for runtime, marker in (("codex", "gpt-"), ("claude", "claude")):
            _, script = agent_run.compile_exe_dev(template, runtime, "x")
            self.assertIn("reflection.int.exe.xyz/integrations", script)
            self.assertIn(f'startswith("{marker}")', script)

    def test_configure_step_needs_no_credential_in_the_template(self):
        template = {
            "name": "t", "runtimes": ["codex"],
            "repos": [{"id": "github.com/o/r"}],
            "setup": ["configure-llm-integration"],
        }
        _, script = agent_run.compile_exe_dev(template, "codex", "x")
        self.assertNotIn("sk-", script)
        self.assertIn("implicit" if False else "int.exe.xyz", script)


class ShippedTemplateTests(unittest.TestCase):
    """Every template in templates/ must stay valid and dispatchable."""

    def test_all_shipped_templates_validate_and_compile(self):
        paths = sorted((ROOT / "templates").glob("*.yaml"))
        self.assertTrue(paths, "no templates found")
        for path in paths:
            with self.subTest(template=path.name):
                template = agent_run.load_template(path)
                for runtime in template["runtimes"]:
                    agent_run.compile_exe_dev(template, runtime, "check")

    def test_no_shipped_template_carries_a_credential(self):
        # Values, not prose: a comment explaining that nothing secret is written
        # is not a secret. Env names are checked separately from string values.
        secret_name = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.I)
        secret_value = re.compile(r"(sk-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|[A-Za-z0-9+/]{40,}={0,2})")

        def strings(node):
            if isinstance(node, str):
                yield node
            elif isinstance(node, dict):
                for value in node.values():
                    yield from strings(value)
            elif isinstance(node, list):
                for item in node:
                    yield from strings(item)

        for path in sorted((ROOT / "templates").glob("*.yaml")):
            template = yaml.safe_load(path.read_text())
            with self.subTest(template=path.name):
                for name in template.get("env", {}):
                    self.assertIsNone(secret_name.search(name), f"env {name} looks like a credential")
                for text in strings(template):
                    self.assertIsNone(secret_value.search(text), f"value looks like a credential: {text[:40]}")


class LlmDiscoveryTests(unittest.TestCase):
    def test_discovery_asks_reflection_rather_than_assuming_a_name(self):
        # `exeuntu configure` targets the integration literally named "llm",
        # which is wrong once providers are split across integrations.
        script = "\n".join(agent_run.render_llm_discovery("codex"))
        self.assertIn("reflection.int.exe.xyz/integrations", script)
        self.assertNotIn("exeuntu configure", script)

    def test_discovery_matches_the_model_family_each_runtime_needs(self):
        self.assertIn('startswith("gpt-")', "\n".join(agent_run.render_llm_discovery("codex")))
        self.assertIn('startswith("claude")', "\n".join(agent_run.render_llm_discovery("claude")))

    def test_discovery_fails_loudly_when_no_integration_serves_the_runtime(self):
        # Silently falling back would look like success while billing the wrong
        # provider, or none at all.
        for runtime in ("codex", "claude"):
            script = "\n".join(agent_run.render_llm_discovery(runtime))
            self.assertIn("exit 1", script)

    def test_discovery_writes_no_credential(self):
        for runtime in ("codex", "claude"):
            script = "\n".join(agent_run.render_llm_discovery(runtime))
            self.assertNotIn("sk-", script)
            self.assertIn("int.exe.xyz", script)
