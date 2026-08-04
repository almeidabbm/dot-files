from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))

import agent_memory as memory


class AgentMemoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_repo(self, name: str, remote: str | None = None) -> Path:
        repo = self.base / name
        repo.mkdir()
        subprocess.run(
            ["git", "init", "-q", str(repo)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if remote:
            subprocess.run(
                ["git", "-C", str(repo), "remote", "add", "origin", remote],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return repo

    def make_legacy_task(
        self,
        repo: Path,
        *,
        slug: str,
        state: str = "active",
        ticket_key: str = "ticket",
        ticket: str = "",
        marker: str = "same",
        missing: str | None = None,
    ) -> Path:
        task = repo / ".local" / state / slug
        task.mkdir(parents=True)
        files = {
            "spec.md": f"# Synthetic task\n\n{marker}\n",
            "plan.md": f"# plan.md\n\n{marker}\n",
            "notes.md": (
                "---\n"
                f"slug: {slug}\n"
                f"{ticket_key}: {ticket}\n"
                "size: standard\n"
                f"status: {state if state == 'active' else 'archived'}\n"
                "last-updated: 2026-01-01T00:00:00Z\n"
                "---\n\n"
                f"{marker}\n"
            ),
            "review.md": f"{marker}\n",
        }
        for name, contents in files.items():
            if name != missing:
                (task / name).write_text(contents, encoding="utf-8")
        return task

    def test_normalizes_common_network_remotes_without_credentials(self) -> None:
        self.assertEqual(
            memory.normalize_remote("git@github.com:Example/Project.git"),
            "github.com/Example/Project",
        )
        self.assertEqual(
            memory.normalize_remote("https://token@example.com/org/repo.git"),
            "example.com/org/repo",
        )
        self.assertEqual(
            memory.normalize_remote("ssh://git@example.com/org/repo.git"),
            "example.com/org/repo",
        )

    def test_memory_root_rejects_broad_and_repository_local_targets(self) -> None:
        repo = self.make_repo("application", "git@example.com:org/application.git")
        with self.assertRaises(memory.AgentMemoryError):
            memory.validate_memory_root(Path("/"))
        with self.assertRaises(memory.AgentMemoryError):
            memory.validate_memory_root(Path.home())
        with self.assertRaises(memory.AgentMemoryError):
            memory.validate_memory_root(repo / ".state", repository=repo)
        external = self.base / "memory"
        self.assertEqual(
            memory.validate_memory_root(external, repository=repo), external.resolve()
        )

    def test_task_can_bind_multiple_repositories(self) -> None:
        app = self.make_repo("application", "git@example.com:org/application.git")
        docs = self.make_repo("documentation", "git@example.com:org/documentation.git")
        root = self.base / "memory"
        task = memory.create_task(
            root,
            slug="2026-01-01-cross-repository-task",
            title="Cross repository task",
            ticket="TRACKER-1",
            size="standard",
            checkout=app,
            role="code",
        )
        manifest = memory.task_manifest(task)
        self.assertIsNotNone(manifest)
        task_id = str(manifest["id"])
        memory.add_repository(root, task_id, docs, "docs")
        updated = memory.task_manifest(task)
        self.assertEqual(
            {item["id"] for item in updated["repositories"]},
            {"example.com/org/application", "example.com/org/documentation"},
        )
        registry = memory.read_json(root / "registry" / "repositories.json", {})
        self.assertEqual(
            {item["id"] for item in registry["repositories"]},
            {"example.com/org/application", "example.com/org/documentation"},
        )
        self.assertEqual(memory.resolve_current_task(root, docs), task)

    def test_system_map_path_is_namespaced_by_repository_identity(self) -> None:
        repo = self.make_repo("application", "git@example.com:org/application.git")
        root = self.base / "memory"
        self.assertEqual(
            memory.safe_repository_path(root, memory.repository_id(repo)) / "system-map",
            (root / "repositories" / "example.com" / "org" / "application" / "system-map").resolve(),
        )

    def test_inventory_collapses_exact_copies_but_not_same_ticket_candidates(self) -> None:
        app = self.make_repo("application", "git@example.com:org/application.git")
        docs = self.make_repo("documentation", "git@example.com:org/documentation.git")
        shared_slug = "2026-01-01-shared-task"
        self.make_legacy_task(app, slug=shared_slug, ticket="TRACKER-1")
        self.make_legacy_task(docs, slug=shared_slug, ticket="TRACKER-1")
        self.make_legacy_task(
            docs,
            slug="2026-01-02-separate-docs-task",
            ticket="TRACKER-2",
            marker="docs",
        )
        self.make_legacy_task(
            app,
            slug="2026-01-02-separate-code-task",
            ticket="TRACKER-2",
            marker="code",
        )

        result = memory.inventory([app, docs], [])
        duplicate_groups = [group for group in result.exact_groups if len(group) > 1]
        self.assertEqual(len(duplicate_groups), 1)
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(len(result.conflicts), 0)

    def test_migration_is_idempotent_and_preserves_sources(self) -> None:
        app = self.make_repo("application", "git@example.com:org/application.git")
        docs = self.make_repo("documentation", "git@example.com:org/documentation.git")
        slug = "2026-01-01-shared-task"
        app_task = self.make_legacy_task(
            app, slug=slug, ticket_key="linear", ticket="TRACKER-1"
        )
        docs_task = self.make_legacy_task(
            docs, slug=slug, ticket_key="linear", ticket="TRACKER-1"
        )
        system_map = app / ".local" / "system-map"
        system_map.mkdir(parents=True)
        (system_map / "inv-example.md").write_text("safe synthetic knowledge\n")
        before = {app_task: memory.hash_tree(app_task), docs_task: memory.hash_tree(docs_task)}
        root = self.base / "memory"

        first_inventory = memory.inventory([app, docs], [])
        first = memory.apply_migration(root, first_inventory)
        second_inventory = memory.inventory([app, docs], [])
        second = memory.apply_migration(root, second_inventory)

        self.assertEqual(first["result"]["imported"], 2)
        self.assertEqual(second["result"]["imported"], 0)
        self.assertEqual(len(memory.task_directories(root)), 1)
        migrated = memory.task_directories(root)[0]
        metadata = memory.parse_frontmatter(migrated / "notes.md")
        self.assertEqual(metadata["ticket"], "TRACKER-1")
        self.assertNotIn("linear", metadata)
        manifest = memory.task_manifest(migrated)
        self.assertEqual(len(manifest["repositories"]), 2)
        for task, original_hash in before.items():
            self.assertEqual(memory.hash_tree(task), original_hash)

    def test_source_change_before_apply_leaves_no_partial_import(self) -> None:
        repo = self.make_repo("application", "git@example.com:org/application.git")
        task = self.make_legacy_task(repo, slug="2026-08-04-changing")
        result = memory.inventory([repo], [])
        (task / "notes.md").write_text(
            (task / "notes.md").read_text(encoding="utf-8") + "changed\n",
            encoding="utf-8",
        )
        root = self.base / "memory"

        with self.assertRaisesRegex(memory.AgentMemoryError, "source task changed"):
            memory.apply_migration(root, result)

        self.assertEqual(list((root / "tasks" / "active").iterdir()), [])

    def test_divergent_same_repository_slug_blocks_apply(self) -> None:
        repo = self.make_repo("application", "git@example.com:org/application.git")
        slug = "2026-01-01-conflicting-task"
        self.make_legacy_task(repo, slug=slug, marker="active")
        self.make_legacy_task(repo, slug=slug, state="archive", marker="archived")
        result = memory.inventory([repo], [])
        self.assertEqual(len(result.conflicts), 1)
        with self.assertRaises(memory.AgentMemoryError):
            memory.apply_migration(self.base / "memory", result)

    def test_incomplete_task_blocks_apply_and_non_task_directory_is_ignored(self) -> None:
        repo = self.make_repo("application", "git@example.com:org/application.git")
        self.make_legacy_task(
            repo,
            slug="2026-01-01-incomplete-task",
            missing="review.md",
        )
        ancillary = repo / ".local" / "active" / ".tool-state"
        ancillary.mkdir(parents=True)
        (ancillary / "data.json").write_text("{}\n")
        result = memory.inventory([repo], [])
        self.assertEqual(len(result.incomplete), 1)
        self.assertEqual(len(result.ignored_entries), 1)
        root = self.base / "memory"
        with self.assertRaises(memory.AgentMemoryError):
            memory.apply_migration(root, result)

        memory.apply_migration(root, result, materialize_missing=True)
        migrated = memory.task_directories(root)[0]
        self.assertIn("Missing from the legacy source", (migrated / "review.md").read_text())
        self.assertEqual(
            memory.task_manifest(migrated)["migration"]["materialized_files"],
            ["review.md"],
        )

    def test_report_is_local_json_and_summary_contains_no_task_content(self) -> None:
        repo = self.make_repo("application", "git@example.com:org/application.git")
        self.make_legacy_task(
            repo,
            slug="2026-01-01-report-task",
            ticket="TRACKER-1",
            marker="private fixture marker",
        )
        result = memory.inventory([repo], [])
        report = memory.migration_report(result, "dry-run", applied=False)
        rendered_summary = json.dumps(report["summary"])
        self.assertNotIn("private fixture marker", rendered_summary)
        self.assertEqual(report["summary"]["tasks"], 1)


if __name__ == "__main__":
    unittest.main()
