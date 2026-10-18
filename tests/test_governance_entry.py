"""Positive loader contract; a negative legacy scan alone cannot prove adoption."""

from pathlib import Path
import unittest


class GovernanceEntryTests(unittest.TestCase):
    def test_project_agents_names_the_canonical_constitution(self):
        entry = Path(__file__).resolve().parents[1] / "AGENTS.md"
        self.assertTrue(entry.is_file(), "The project AGENTS loader is required")
        self.assertTrue(
            "https://github.com/MrWizard94-Compile/Agents-Constitution"
            in entry.read_text(encoding="utf-8"),
            "Project instructions must name the canonical law source",
        )


if __name__ == "__main__":
    unittest.main()
