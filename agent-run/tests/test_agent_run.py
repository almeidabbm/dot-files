import argparse
import base64
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent

loader = importlib.machinery.SourceFileLoader("agent_run", str(ROOT / "bin" / "agent-run"))
spec = importlib.util.spec_from_loader("agent_run", loader)
agent_run = importlib.util.module_from_spec(spec)
loader.exec_module(agent_run)

TEMPLATE = ROOT / "templates" / "lightdash-dev.yaml"


def write_yaml(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    f.write(content)
    f.close()
    return f.name


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class ValidateTests(unittest.TestCase):
    def test_example_template_is_valid(self):
        template = agent_run.load_template(TEMPLATE)
        self.assertEqual(template["name"], "lightdash-dev")

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
        return agent_run.compile_exe_dev(template, runtime, f"lightdash-dev-{runtime}")

    def test_command_carries_template_settings(self):
        argv, _ = self.compile()
        command = agent_run.display_command(argv, "setup.sh")
        for expected in [
            "ssh exe.dev new --json",
            "--name=lightdash-dev-codex",
            "--cpu=4",
            "--memory=8GB",
            "--disk=50GB",
            "--image=exeuntu",
            "--env=NODE_ENV=development",
            "--integration=github",
            "--tag=agent-pilot",
            "--comment=agent-run:lightdash-dev:codex",
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
        self.assertIn("--comment=agent-run:lightdash-dev:claude", argv)
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

    def test_public_clone_url_without_github_integration(self):
        template = agent_run.load_template(TEMPLATE)
        template["providers"]["exe.dev"]["integrations"] = []
        _, script = agent_run.compile_exe_dev(template, "codex", "x")
        self.assertIn("https://github.com/lightdash/lightdash.git", script)


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
            completed(stdout="ready\n"),
            completed(),
        ]
        pushed = {}

        def fake_sh(args, input_text=None, check=True):
            command = args[-1]
            if "base64 -d > ~/work/TASK.md" in command:
                # the gateway drops stdin, so content must ride in the command
                self.assertIsNone(input_text)
                self.assertEqual(args[-2], "task-a")  # exec targets the VM name
                encoded = command.split()[1]
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
                agent_run.cmd_status(argparse.Namespace(offline=False))
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
                agent_run.cmd_status(argparse.Namespace(offline=False))

        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertEqual(record["status"], "ready")
        self.assertEqual(record["ready_at"], "2026-08-11T00:15:00Z")

    def test_logs_shows_setup_journal_tail(self):
        self.seed_run()
        log = completed(stdout="line1\nline2\nline3\n")
        with mock.patch.object(agent_run, "sh", return_value=log):
            with mock.patch("builtins.print") as fake_print:
                agent_run.cmd_logs(argparse.Namespace(name="task-a", lines=2))
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
