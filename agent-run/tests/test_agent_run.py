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
MULTI_REPO = ROOT / "tests" / "fixtures" / "multi-repo.yaml"


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
    defaults = dict(name=name, prompt_file=None, sandbox="workspace-write", force=False, interactive=False)
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


class MultiRepoTests(unittest.TestCase):
    def compile(self, template=None):
        template = template or agent_run.load_template(MULTI_REPO)
        return agent_run.compile_exe_dev(template, "codex", "multi")

    def test_colliding_checkout_paths_are_refused(self):
        # Both would clone to "$WORK/api" and the second would fail deep in the
        # setup journal, long after dispatch reported success.
        path = write_yaml(
            "version: 1\nname: collide\nruntimes: [codex]\nrepos:\n"
            "  - id: github.com/org-a/api\n    role: primary\n"
            "  - id: github.com/org-b/api\n"
        )
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.load_template(path)
        message = str(ctx.exception)
        self.assertIn("github.com/org-a/api", message)
        self.assertIn("github.com/org-b/api", message)
        self.assertIn("path:", message)

    def test_an_explicit_path_resolves_a_collision(self):
        path = write_yaml(
            "version: 1\nname: fine\nruntimes: [codex]\nrepos:\n"
            "  - id: github.com/org-a/api\n    role: primary\n"
            "  - id: github.com/org-b/api\n    path: api-b\n"
        )
        self.assertEqual(len(agent_run.load_template(path)["repos"]), 2)

    def test_several_repos_with_no_primary_are_refused(self):
        # Otherwise the agent starts in whichever repo happens to be declared
        # first, which is an ordering accident rather than a decision.
        path = write_yaml(
            "version: 1\nname: nohome\nruntimes: [codex]\nrepos:\n"
            "  - id: github.com/o/a\n  - id: github.com/o/b\n"
        )
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.load_template(path)
        self.assertIn("role: primary", str(ctx.exception))

    def test_two_primaries_are_refused(self):
        path = write_yaml(
            "version: 1\nname: twohomes\nruntimes: [codex]\nrepos:\n"
            "  - id: github.com/o/a\n    role: primary\n"
            "  - id: github.com/o/b\n    role: primary\n"
        )
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.load_template(path)
        self.assertIn("only one repo", str(ctx.exception))

    def test_a_single_repo_still_needs_no_primary_marker(self):
        # The fallback stays safe precisely because ambiguity is refused above.
        path = write_yaml(
            "version: 1\nname: solo\nruntimes: [codex]\nrepos:\n  - id: github.com/o/only\n"
        )
        template = agent_run.load_template(path)
        self.assertEqual(agent_run.primary_workdir(template), "~/work/only")

    def test_every_repo_is_cloned(self):
        _, script = self.compile()
        self.assertIn('https://github.int.exe.xyz/lightdash/lightdash.git "$WORK"/lightdash', script)
        self.assertIn('https://github.com/almeidabbm/dot-files.git "$WORK"/dot-files', script)

    def test_per_repo_steps_run_in_their_own_checkout(self):
        _, script = self.compile()
        self.assertIn('( cd "$WORK"/lightdash && pnpm install --frozen-lockfile )', script)
        self.assertIn('( cd "$WORK"/dot-files && python3 -m pip install --user jsonschema pyyaml )', script)

    def test_template_wide_steps_precede_the_per_repo_ones(self):
        # The template-wide list is machine-level provisioning; a repo's own
        # install is the thing that depends on it, so it cannot run first.
        _, script = self.compile()
        self.assertLess(
            script.index("echo cross-repo step"),
            script.index("pnpm install --frozen-lockfile"),
        )

    def test_per_repo_steps_precede_the_checks(self):
        _, script = self.compile()
        self.assertLess(
            script.index("pnpm install --frozen-lockfile"),
            script.index("git --version"),
        )

    def test_clones_precede_every_setup_step(self):
        _, script = self.compile()
        self.assertLess(
            script.index('"$WORK"/dot-files\n'),  # the clone, not the cd
            script.index("pnpm install --frozen-lockfile"),
        )


class ManifestTests(unittest.TestCase):
    def manifest(self):
        _, script = agent_run.compile_exe_dev(agent_run.load_template(MULTI_REPO), "codex", "m")
        body = script.split("<<'REPOSMD'\n", 1)[1].split("\nREPOSMD", 1)[0]
        return body

    def test_manifest_lists_every_checkout_with_its_repo(self):
        body = self.manifest()
        self.assertIn("`~/work/lightdash` | github.com/lightdash/lightdash", body)
        self.assertIn("`~/work/dot-files` | github.com/almeidabbm/dot-files", body)

    def test_manifest_marks_exactly_one_primary(self):
        rows = [l for l in self.manifest().splitlines() if l.startswith("| `~/work/")]
        primary = [r for r in rows if r.endswith("| primary |")]
        self.assertEqual(len(primary), 1)
        self.assertIn("github.com/lightdash/lightdash", primary[0])

    def test_manifest_names_a_repo_with_no_ref(self):
        # An unpinned checkout is on the remote's default branch; saying so beats
        # an empty cell the agent has to interpret.
        self.assertIn("| (default) |", self.manifest())

    def test_manifest_is_a_quoted_heredoc_so_set_x_cannot_echo_it(self):
        _, script = agent_run.compile_exe_dev(agent_run.load_template(MULTI_REPO), "codex", "m")
        self.assertIn("<<'REPOSMD'", script)

    def test_single_repo_template_still_gets_a_manifest(self):
        _, script = agent_run.compile_exe_dev(agent_run.load_template(TEMPLATE), "codex", "m")
        self.assertIn("REPOS.md", script)
        self.assertIn("| primary |", script)


class RunStateTestCase(unittest.TestCase):
    """Base class giving each test an isolated state root."""

    def setUp(self):
        self.state_dir = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"AGENT_RUN_STATE_PATH": self.state_dir.name})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.state_dir.cleanup)


SECRETS_TEMPLATE = """version: 1
name: sec
runtimes: [codex]
secrets:
  - name: GITHUB_TOKEN
    type: git-credential
    host: github.com
  - name: NPM_TOKEN
    type: file
    path: .npmrc
    format: "//registry.npmjs.org/:_authToken={{value}}"
repos:
  - id: github.com/o/private-thing
    role: primary
    auth: GITHUB_TOKEN
"""

# Distinctive enough that finding it anywhere is unambiguous.
FAKE_TOKEN = "ghp_TESTTOKENVALUE0000000000000000000000"


def token_source(value=FAKE_TOKEN, exit_code=0):
    """A resolver command that fetches the token rather than containing it.

    The command itself is stored config and is printed back by `secret ls`, so a
    command with the credential baked in would make every leak assertion below
    vacuous — and is the thing a real user must not do either.
    """
    f = tempfile.NamedTemporaryFile("w", delete=False)
    f.write(value + "\n")
    f.close()
    suffix = f"; exit {exit_code}" if exit_code else ""
    return f"cat {f.name}{suffix}"


class SecretDeclarationTests(unittest.TestCase):
    def test_token_shaped_env_is_refused_and_points_at_secrets(self):
        # env becomes --env=K=V: provider metadata, and the agent's own環境.
        for name in ("GITHUB_TOKEN", "NPM_SECRET", "DB_PASSWORD", "SOME_API_KEY"):
            path = write_yaml(
                "version: 1\nname: leaky\nruntimes: [codex]\n"
                f"repos:\n  - id: github.com/a/b\nenv:\n  {name}: value\n"
            )
            with self.assertRaises(agent_run.TemplateError) as ctx:
                agent_run.load_template(path)
            self.assertIn("secrets:", str(ctx.exception))

    def test_ordinary_env_still_passes(self):
        path = write_yaml(
            "version: 1\nname: fine\nruntimes: [codex]\n"
            "repos:\n  - id: github.com/a/b\nenv:\n  NODE_ENV: development\n"
        )
        self.assertEqual(agent_run.load_template(path)["env"], {"NODE_ENV": "development"})

    def test_auth_naming_an_undeclared_secret_is_refused(self):
        path = write_yaml(
            "version: 1\nname: undeclared\nruntimes: [codex]\n"
            "repos:\n  - id: github.com/o/r\n    auth: NOPE\n"
        )
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.load_template(path)
        self.assertIn("no 'secrets:' entry declares", str(ctx.exception))

    def test_auth_and_private_together_are_refused(self):
        # They are two different routes to the same repo; silently preferring
        # one would make the other look broken.
        path = write_yaml(
            SECRETS_TEMPLATE.replace("    auth: GITHUB_TOKEN", "    auth: GITHUB_TOKEN\n    private: true")
        )
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.load_template(path)
        self.assertIn("Pick one", str(ctx.exception))

    def test_credential_for_the_wrong_host_is_refused(self):
        # The store helper matches on host, so this would never be offered and
        # the clone would sit waiting for a password nobody can type.
        path = write_yaml(SECRETS_TEMPLATE.replace("host: github.com", "host: gitlab.com"))
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.load_template(path)
        self.assertIn("matches on host", str(ctx.exception))

    def test_auth_against_a_file_secret_is_refused(self):
        path = write_yaml(SECRETS_TEMPLATE.replace("auth: GITHUB_TOKEN", "auth: NPM_TOKEN"))
        with self.assertRaises(agent_run.TemplateError) as ctx:
            agent_run.load_template(path)
        self.assertIn("git-credential", str(ctx.exception))

    def test_an_auth_repo_clones_from_the_ordinary_url(self):
        # A token in the URL would be written into .git/config and survive there.
        template = agent_run.load_template(write_yaml(SECRETS_TEMPLATE))
        _, script = agent_run.compile_exe_dev(template, "codex", "x")
        self.assertIn("https://github.com/o/private-thing.git", script)
        self.assertNotIn("@github.com/o/private-thing", script)


class SecretStoreTests(RunStateTestCase):
    def test_set_stores_the_command_and_never_the_value(self):
        agent_run.cmd_secret_set(argparse.Namespace(
            name="GITHUB_TOKEN", command=token_source()))
        stored = agent_run.secrets_config_path().read_text()
        self.assertIn("cat ", stored)
        self.assertNotIn(FAKE_TOKEN, stored)

    def test_the_store_is_not_world_readable(self):
        agent_run.cmd_secret_set(argparse.Namespace(name="T", command="echo v"))
        self.assertEqual(agent_run.secrets_config_path().stat().st_mode & 0o077, 0)

    def test_set_refuses_a_command_that_does_not_work(self):
        with self.assertRaises(agent_run.RunError):
            agent_run.cmd_secret_set(argparse.Namespace(name="T", command="exit 3"))
        self.assertFalse(agent_run.secrets_config_path().exists())

    def test_set_refuses_a_command_that_prints_nothing(self):
        with self.assertRaises(agent_run.RunError) as ctx:
            agent_run.cmd_secret_set(argparse.Namespace(name="T", command="true"))
        self.assertIn("produced nothing", str(ctx.exception))

    def test_a_failing_resolver_never_echoes_its_output(self):
        # A partially-written credential is still a credential.
        agent_run.save_secret_config({"T": {"command": token_source(exit_code=1)}})
        with self.assertRaises(agent_run.RunError) as ctx:
            agent_run.resolve_secret("T")
        self.assertNotIn(FAKE_TOKEN, str(ctx.exception))

    def test_multi_line_output_is_refused(self):
        agent_run.save_secret_config({"T": {"command": "printf 'a\\nb\\n'"}})
        with self.assertRaises(agent_run.RunError) as ctx:
            agent_run.resolve_secret("T")
        self.assertIn("several lines", str(ctx.exception))

    def test_ls_shows_names_and_commands_but_no_values(self):
        agent_run.save_secret_config({"GITHUB_TOKEN": {"command": token_source()}})
        with mock.patch("builtins.print") as fake_print:
            agent_run.cmd_secret_ls(argparse.Namespace())
        output = "\n".join(str(c.args[0]) for c in fake_print.call_args_list if c.args)
        self.assertIn("GITHUB_TOKEN", output)
        self.assertIn("ok", output)
        self.assertNotIn(FAKE_TOKEN, output)

    def test_ls_reports_a_resolver_that_has_stopped_working(self):
        agent_run.save_secret_config({"T": {"command": "exit 1"}})
        with mock.patch("builtins.print") as fake_print:
            agent_run.cmd_secret_ls(argparse.Namespace())
        output = "\n".join(str(c.args[0]) for c in fake_print.call_args_list if c.args)
        self.assertIn("FAILS", output)

    def test_a_literal_resolver_is_warned_about(self):
        # `--command 'echo hunter2'` puts the value back at rest in the config,
        # which is the one thing this store exists to avoid.
        with mock.patch("builtins.print") as fake_print:
            agent_run.cmd_secret_set(argparse.Namespace(name="T", command="echo hunter2"))
        output = "\n".join(str(c.args[0]) for c in fake_print.call_args_list if c.args)
        self.assertIn("credential at rest", output)

    def test_a_fetching_resolver_is_not_warned_about(self):
        with mock.patch("builtins.print") as fake_print:
            agent_run.cmd_secret_set(argparse.Namespace(name="T", command=token_source()))
        output = "\n".join(str(c.args[0]) for c in fake_print.call_args_list if c.args)
        self.assertNotIn("warning", output)

    def test_unregistered_secret_names_the_fix(self):
        with self.assertRaises(agent_run.RunError) as ctx:
            agent_run.resolve_secret("MISSING")
        self.assertIn("agent-run secret set MISSING", str(ctx.exception))


class SecretRenderingTests(unittest.TestCase):
    def secrets(self):
        return agent_run.load_template(write_yaml(SECRETS_TEMPLATE))["secrets"]

    def test_the_installer_carries_no_credential(self):
        script = agent_run.render_install_secrets(self.secrets())
        self.assertNotIn(FAKE_TOKEN, script)
        self.assertIn('VALUE="$(cat "$SECRETS"/GITHUB_TOKEN)"', script)

    def test_the_installer_never_turns_on_tracing(self):
        # The boot script runs under `set -x`; this one must not, or every
        # expansion lands in the journal that `logs --source setup` prints.
        script = agent_run.render_install_secrets(self.secrets())
        self.assertIn("set -eu\n", script)
        self.assertNotIn("set -x", script)
        self.assertNotIn("-eux", script)

    def test_git_credentials_is_written_restricted(self):
        script = agent_run.render_install_secrets(self.secrets())
        self.assertIn("umask 077", script)
        self.assertIn('chmod 600 "$HOME"/.git-credentials', script)
        self.assertIn("credential.helper store", script)
        self.assertIn('"https://x-access-token:$VALUE@github.com"', script)

    def test_a_file_secret_uses_its_format(self):
        script = agent_run.render_install_secrets(self.secrets())
        self.assertIn('"//registry.npmjs.org/:_authToken=$VALUE"', script)
        self.assertIn('chmod 600 "$HOME"/.npmrc', script)

    def test_the_boot_script_waits_before_it_clones(self):
        template = agent_run.load_template(write_yaml(SECRETS_TEMPLATE))
        _, script = agent_run.compile_exe_dev(template, "codex", "x")
        self.assertLess(
            script.index(".agent-run-awaiting-secrets"),
            script.index("git clone"),
        )

    def test_the_boot_script_turns_tracing_off_around_the_installer(self):
        template = agent_run.load_template(write_yaml(SECRETS_TEMPLATE))
        _, script = agent_run.compile_exe_dev(template, "codex", "x")
        lines = script.splitlines()
        install = next(i for i, l in enumerate(lines) if "install-secrets.sh" in l)
        self.assertEqual(lines[install - 1].strip(), "set +x")
        self.assertEqual(lines[install + 1].strip(), "set -x")

    def test_a_template_with_no_secrets_gains_no_handshake(self):
        _, script = agent_run.compile_exe_dev(agent_run.load_template(TEMPLATE), "codex", "x")
        self.assertNotIn("awaiting-secrets", script)

    def test_the_creation_command_never_carries_a_secret(self):
        template = agent_run.load_template(write_yaml(SECRETS_TEMPLATE))
        argv, script = agent_run.compile_exe_dev(template, "codex", "x")
        self.assertNotIn("GITHUB_TOKEN", " ".join(argv))
        # The name may appear in the script (it names a file); the value never can,
        # because compile has not resolved anything.
        self.assertNotIn(FAKE_TOKEN, script)


class SecretDeliveryTests(RunStateTestCase):
    def dispatch_args(self, template_path, **overrides):
        defaults = dict(
            template=template_path, provider="exe.dev", runtime="codex", name="task-a",
            prompt_file=None, no_wait=False, wait_timeout=60, poll_interval=0,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def register(self):
        agent_run.save_secret_config({
            "GITHUB_TOKEN": {"command": token_source()},
            "NPM_TOKEN": {"command": "echo npm-value"},
        })

    def run_dispatch(self):
        """Dispatch against a fake provider; returns every command sent."""
        self.register()
        path = write_yaml(SECRETS_TEMPLATE)
        sent = []

        def fake_sh(args, input_text=None, check=True):
            sent.append((args, input_text))
            command = args[-1]
            if args[:3] == ["ssh", "exe.dev", "new"]:
                return completed(stdout=json.dumps({"vm_name": "task-a", "ssh_dest": "u@vm"}))
            if "awaiting-secrets" in command:
                return completed(stdout="PRESENT\n")
            if "agent-run-ready" in command:
                return completed(stdout="2026-08-14T07:00:00Z\n")
            return completed()

        with mock.patch.object(agent_run, "sh", fake_sh), mock.patch("builtins.print"):
            with mock.patch.object(agent_run.time, "sleep"):
                agent_run.cmd_dispatch(self.dispatch_args(path))
        return sent

    def test_the_value_reaches_the_vm_base64_encoded(self):
        sent = self.run_dispatch()
        pushes = [a[-1] for a, _ in sent if "base64 -d > ~/.agent-run/secrets/GITHUB_TOKEN" in a[-1]]
        self.assertEqual(len(pushes), 1)
        encoded = pushes[0].split("echo ")[1].split()[0]
        self.assertEqual(base64.b64decode(encoded).decode().strip(), FAKE_TOKEN)

    def test_the_value_is_never_sent_in_the_clear(self):
        # Everything else — the creation call, the setup script, every other
        # remote command — must be free of it.
        for args, input_text in self.run_dispatch():
            command = args[-1]
            if "base64 -d > ~/.agent-run/secrets/" in command:
                continue
            self.assertNotIn(FAKE_TOKEN, command)
            self.assertNotIn(FAKE_TOKEN, input_text or "")

    def test_secrets_land_restricted(self):
        sent = self.run_dispatch()
        push = next(a[-1] for a, _ in sent if "secrets/GITHUB_TOKEN" in a[-1])
        self.assertIn("umask 077", push)
        self.assertIn("chmod 600 ~/.agent-run/secrets/GITHUB_TOKEN", push)

    def test_the_completion_marker_is_written_last(self):
        # The boot script wakes on it, so anything written after it is a race.
        commands = [a[-1] for a, _ in self.run_dispatch() if a[:3] == ["ssh", "exe.dev", "ssh"] or "ssh" in a]
        touch = next(i for i, c in enumerate(commands) if "touch ~/.agent-run/secrets/.complete" in c)
        installer = next(i for i, c in enumerate(commands) if "install-secrets.sh" in c)
        value = next(i for i, c in enumerate(commands) if "secrets/GITHUB_TOKEN" in c)
        self.assertLess(value, touch)
        self.assertLess(installer, touch)

    def test_the_run_record_stores_names_not_values(self):
        self.run_dispatch()
        record = agent_run.run_record_path("task-a").read_text()
        self.assertIn("GITHUB_TOKEN", record)
        self.assertNotIn(FAKE_TOKEN, record)

    def test_an_unregistered_secret_fails_before_any_vm_exists(self):
        # Otherwise the VM boots and blocks forever on secrets that never come.
        path = write_yaml(SECRETS_TEMPLATE)
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(args)
            return completed()

        with mock.patch.object(agent_run, "sh", fake_sh):
            with self.assertRaises(agent_run.RunError):
                agent_run.cmd_dispatch(self.dispatch_args(path))
        self.assertEqual(calls, [])

    def test_no_wait_is_refused_when_the_boot_script_would_block(self):
        self.register()
        path = write_yaml(SECRETS_TEMPLATE)
        with self.assertRaises(agent_run.RunError) as ctx:
            agent_run.cmd_dispatch(self.dispatch_args(path, no_wait=True))
        self.assertIn("strand", str(ctx.exception))


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
        for line in script.splitlines():
            self.assertFalse(line.rstrip().endswith("&"), f"backgrounded: {line}")
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
            if "test -s" in args[-1]:
                return completed(stdout="PRESENT\n")
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

    def test_attach_goes_direct_because_the_gateway_gives_no_tty(self):
        # `ssh -tt exe.dev ssh <vm> tty` reports "not a tty", so tmux through the
        # gateway fails with "open terminal failed: not a terminal".
        self.assertEqual(
            agent_run.attach_argv("task-a.exe.xyz"),
            ["ssh", "-t", "-o", "StrictHostKeyChecking=accept-new",
             "task-a.exe.xyz", "tmux", "attach", "-t", "agent"],
        )

    def test_follow_stays_on_the_gateway(self):
        # Streaming needs no TTY, and a direct call with a command can land in
        # the exe.dev REPL.
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


class DispatchNextStepsTests(RunStateTestCase):
    def dispatch_with(self, setup_steps):
        path = write_yaml(
            "version: 1\nname: probe-tpl\nruntimes: [codex]\n"
            "repos:\n  - id: github.com/o/r\n"
            + ("setup:\n" + "".join(f"  - {s}\n" for s in setup_steps) if setup_steps else "")
        )
        responses = [
            completed(stdout=json.dumps({"vm_name": "t", "ssh_dest": "u@vm"})),
            completed(stdout="2026-08-14T06:00:00Z\n"),
        ]
        printed = []
        args = argparse.Namespace(
            template=path, provider="exe.dev", runtime="codex", name="t",
            prompt_file=None, no_wait=False, wait_timeout=60, poll_interval=1,
        )
        with mock.patch.object(agent_run, "sh", lambda *a, **k: responses.pop(0)):
            with mock.patch("builtins.print", lambda *a, **k: printed.append(str(a[0]) if a else "")):
                agent_run.cmd_dispatch(args)
        return "\n".join(printed)

    def test_configured_template_points_at_run_not_a_login(self):
        # Discovery already configured the runtime; telling a human to log in
        # would send them chasing an authentication problem that is not there.
        out = self.dispatch_with(["configure-llm-integration"])
        self.assertIn("agent-run run t", out)
        self.assertNotIn("login", out)

    def test_unconfigured_template_still_asks_for_a_login(self):
        out = self.dispatch_with([])
        self.assertIn("login", out)


class TagScopedKeyHintTests(unittest.TestCase):
    def test_integration_refusal_explains_both_ways_out(self):
        fake = completed(returncode=1, stdout='{"error":"tag-scoped SSH keys cannot modify integrations"}')
        with mock.patch.object(agent_run, "sh", side_effect=agent_run.RunError(fake.stdout)):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.create_vm(["ssh", "exe.dev", "new"], "script")
        message = str(ctx.exception)
        self.assertIn("auto:all", message)
        self.assertIn("ssh-key add", message)

    def test_tag_refusal_points_at_the_template_field(self):
        with mock.patch.object(
            agent_run, "sh",
            side_effect=agent_run.RunError('{"error":"--tag SSH key scoped to tag \\"x\\" can only use --tag=x"}'),
        ):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.create_vm(["ssh", "exe.dev", "new"], "script")
        self.assertIn("tags:", str(ctx.exception))

    def test_unrelated_errors_pass_through_unchanged(self):
        with mock.patch.object(agent_run, "sh", side_effect=agent_run.RunError("quota exceeded")):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.create_vm(["ssh", "exe.dev", "new"], "script")
        self.assertEqual(str(ctx.exception), "quota exceeded")


class PromptRequiredTests(RunStateTestCase):
    def seed(self, **extra):
        record = {
            "name": "task-a", "vm": "task-a", "ssh_dest": "u@vm", "provider": "exe.dev",
            "template": "t.yaml", "runtime": "codex", "status": "ready",
            "created_at": "2026-08-14T06:00:00Z", "workdir": "~/work/repo",
        }
        record.update(extra)
        agent_run.save_run(record)

    def test_run_without_a_prompt_refuses_when_the_vm_has_none(self):
        # Otherwise the runtime answers "what would you like me to work on?"
        # and exits 0 — a no-op that looks like success.
        self.seed()
        with mock.patch.object(agent_run, "sh", lambda *a, **k: completed(stdout="")):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.cmd_run(run_args("task-a"))
        self.assertIn("--prompt-file", str(ctx.exception))

    def test_run_without_a_prompt_proceeds_when_an_earlier_run_left_one(self):
        self.seed()
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(args[-1])
            if "test -s" in args[-1]:
                return completed(stdout="PRESENT\n")
            return completed(stdout="DONE:0\n")

        with mock.patch.object(agent_run, "sh", fake_sh):
            agent_run.cmd_run(run_args("task-a"))
        self.assertTrue(any("tmux new-session" in c for c in calls))

    def test_runner_refuses_an_empty_prompt_with_a_nonzero_exit(self):
        script = agent_run.render_runner("codex", "workspace-write", "~/work/repo")
        self.assertIn("no task prompt", script)
        self.assertIn("exit 2", script)


class InteractiveAndShellTests(RunStateTestCase):
    def seed(self, **extra):
        record = {
            "name": "task-a", "vm": "task-a", "ssh_dest": "u@vm", "provider": "exe.dev",
            "template": "t.yaml", "runtime": "codex", "status": "ready",
            "created_at": "2026-08-14T06:00:00Z", "workdir": "~/work/repo",
        }
        record.update(extra)
        agent_run.save_run(record)

    def test_interactive_needs_no_prompt(self):
        self.seed()
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(args[-1])
            return completed(stdout="DONE:0\n")

        with mock.patch.object(agent_run, "sh", fake_sh):
            agent_run.cmd_run(run_args("task-a", interactive=True))
        self.assertFalse(any("test -s" in c for c in calls), "must not demand a prompt")
        self.assertTrue(any("tmux new-session" in c for c in calls))

    def test_interactive_rejects_a_prompt_file(self):
        self.seed()
        with self.assertRaises(agent_run.RunError) as ctx:
            agent_run.cmd_run(run_args("task-a", interactive=True, prompt_file="/tmp/x.md"))
        self.assertIn("--interactive", str(ctx.exception))

    def test_interactive_runner_reads_no_prompt_and_captures_no_log(self):
        script = agent_run.render_runner("codex", "workspace-write", "~/work/repo", interactive=True)
        self.assertNotIn("TASK.md", script)
        self.assertNotIn("tee", script)          # a TUI through tee is unreadable
        self.assertIn("codex --sandbox workspace-write", script)
        self.assertIn(agent_run.shell_path(agent_run.AGENT_EXIT_REMOTE), script)

    def test_interactive_runner_maps_sandbox_for_claude_too(self):
        script = agent_run.render_runner("claude", "danger-full-access", "~/work/repo", interactive=True)
        self.assertIn("claude --permission-mode bypassPermissions", script)

    def test_shell_targets_the_vm_directly_with_a_tty(self):
        argv = agent_run.shell_argv("task-a.exe.xyz")
        self.assertEqual(argv[0], "ssh")
        self.assertIn("-t", argv)
        self.assertEqual(argv[-1], "task-a.exe.xyz")
        self.assertNotIn("exe.dev", argv)  # the gateway cannot give a TTY

    def test_shell_refuses_a_deleted_run(self):
        self.seed(status="deleted")
        with self.assertRaises(agent_run.RunError):
            agent_run.cmd_shell(argparse.Namespace(name="task-a"))

    def test_attach_failure_names_the_alternatives(self):
        self.seed(started_at="2026-08-14T06:01:00Z")
        with mock.patch.object(agent_run, "sh", lambda *a, **k: completed(stdout="DONE:0\n")):
            with self.assertRaises(agent_run.RunError) as ctx:
                agent_run.cmd_attach(argparse.Namespace(name="task-a"))
        message = str(ctx.exception)
        self.assertIn("--interactive", message)
        self.assertIn("agent-run shell", message)


class StatTests(RunStateTestCase):
    def test_format_leads_with_memory_and_flags_pressure(self):
        # exe.dev's own stat table omits memory, and memory is what kills a
        # build on an 8GB box.
        lines = "\n".join(agent_run.format_stat({
            "cpu_cores": 2.0, "cpu_nominal": 4,
            "mem_used_bytes": 8_350_076_928, "mem_total_bytes": 8_589_934_592,
            "fs_used_gb": 5.5, "fs_total_gb": 53.7,
        }))
        self.assertIn("memory", lines)
        self.assertIn("tight", lines)
        self.assertIn("cpu", lines)

    def test_no_pressure_flag_when_memory_is_comfortable(self):
        lines = "\n".join(agent_run.format_stat({
            "mem_used_bytes": 2_000_000_000, "mem_total_bytes": 8_589_934_592,
        }))
        self.assertNotIn("tight", lines)

    def test_latest_sample_wins_regardless_of_order(self):
        payload = json.dumps({"points": [
            {"timestamp": "2026-08-14T12:10:26Z", "cpu_cores": 3},
            {"timestamp": "2026-08-14T06:28:35Z", "cpu_cores": 1},
        ]})
        with mock.patch.object(agent_run, "sh", lambda *a, **k: completed(stdout=payload)):
            self.assertEqual(agent_run.latest_stat("vm")["cpu_cores"], 3)

    def test_unreadable_metrics_are_not_faked(self):
        with mock.patch.object(agent_run, "sh", lambda *a, **k: completed(returncode=1)):
            self.assertIsNone(agent_run.latest_stat("vm"))

    def test_tokens_read_the_last_total_the_runtime_printed(self):
        log = "tokens used\n9,031\nmore work\ntokens used\n36,756\n"
        with mock.patch.object(agent_run, "sh", lambda *a, **k: completed(stdout=log)):
            self.assertEqual(agent_run.agent_tokens({"vm": "v", "agent_log": "~/x"}), 36756)


class ResourcesWindowTests(unittest.TestCase):
    def test_resources_window_survives_a_refresh(self):
        # It is not a run, so a naive prune would close it every time.
        add, kill = agent_run.plan_monitor_windows(
            ["a", agent_run.RESOURCES_WINDOW], ["a", agent_run.RESOURCES_WINDOW]
        )
        self.assertEqual((add, kill), ([], []))

    def test_resources_window_name_cannot_collide_with_a_run(self):
        # Run names come from --name, which the schema restricts to [a-z0-9-].
        self.assertIn(".", agent_run.RESOURCES_WINDOW)

    def test_resources_command_loops_over_every_run(self):
        command = agent_run.resources_cmd(["alpha", "beta"])
        self.assertIn("stat alpha", command)
        self.assertIn("stat beta", command)
        self.assertIn("while true", command)


class StopTests(RunStateTestCase):
    def seed(self, **extra):
        record = {
            "name": "task-a", "vm": "task-a", "ssh_dest": "u@vm", "provider": "exe.dev",
            "template": "t.yaml", "runtime": "codex", "status": "ready",
            "created_at": "2026-08-14T06:00:00Z", "started_at": "2026-08-14T06:01:00Z",
        }
        record.update(extra)
        agent_run.save_run(record)

    def test_stop_kills_the_session_and_records_an_exit_code(self):
        # Killing tmux means the runner never writes one, and a run with no exit
        # code reads as exited(?) — indistinguishable from a crash.
        self.seed()
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(args[-1])
            return completed(stdout="RUNNING\n")

        with mock.patch.object(agent_run, "sh", fake_sh), mock.patch("builtins.print"):
            agent_run.cmd_stop(argparse.Namespace(name="task-a"))

        self.assertTrue(any("tmux kill-session -t agent" in c for c in calls))
        self.assertTrue(any(str(agent_run.STOPPED_EXIT_CODE) in c and "agent-run-exit" in c for c in calls))
        record = json.loads(agent_run.run_record_path("task-a").read_text())
        self.assertTrue(record["stopped_at"])

    def test_stop_leaves_the_vm_alone(self):
        self.seed()
        calls = []

        def fake_sh(args, input_text=None, check=True):
            calls.append(" ".join(args))
            return completed(stdout="RUNNING\n")

        with mock.patch.object(agent_run, "sh", fake_sh), mock.patch("builtins.print"):
            agent_run.cmd_stop(argparse.Namespace(name="task-a"))
        self.assertFalse(any(" rm " in c for c in calls), "stop must not delete the VM")

    def test_stopping_an_idle_run_is_not_an_error(self):
        self.seed()
        with mock.patch.object(agent_run, "sh", lambda *a, **k: completed(stdout="DONE:0\n")):
            with mock.patch("builtins.print") as fake_print:
                agent_run.cmd_stop(argparse.Namespace(name="task-a"))
        self.assertIn("no agent to stop", " ".join(str(c.args[0]) for c in fake_print.call_args_list if c.args))

    def test_stop_refuses_a_deleted_run(self):
        self.seed(status="deleted")
        with self.assertRaises(agent_run.RunError):
            agent_run.cmd_stop(argparse.Namespace(name="task-a"))
