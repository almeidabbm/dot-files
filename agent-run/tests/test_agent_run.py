import importlib.machinery
import importlib.util
import pathlib
import tempfile
import unittest

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
        return agent_run.compile_exe_dev(
            template, runtime, f"lightdash-dev-{runtime}", "setup.sh"
        )

    def test_command_carries_template_settings(self):
        command, _ = self.compile()
        for expected in [
            "ssh exe.dev new --json",
            "--name=lightdash-dev-codex",
            "--cpu=4",
            "--memory=8GB",
            "--disk=50GB",
            "--image=exeuntu",
            "--env NODE_ENV=development",
            "--integration=github",
            "--tag=agent-pilot",
            "--tag=runtime-codex",
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
        command, script = self.compile("claude")
        self.assertIn("--tag=runtime-claude", command)
        self.assertIn("sudo exeuntu update claude", script)
        self.assertNotIn("update codex", script)

    def test_disallowed_runtime_rejected(self):
        template = agent_run.load_template(TEMPLATE)
        template["runtimes"] = ["codex"]
        with self.assertRaises(agent_run.TemplateError):
            agent_run.compile_exe_dev(template, "claude", "x", "setup.sh")

    def test_public_clone_url_without_github_integration(self):
        template = agent_run.load_template(TEMPLATE)
        template["providers"]["exe.dev"]["integrations"] = []
        _, script = agent_run.compile_exe_dev(template, "codex", "x", "setup.sh")
        self.assertIn("https://github.com/lightdash/lightdash.git", script)


if __name__ == "__main__":
    unittest.main()
