import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runit.runit import getopt


class GetoptTests(unittest.TestCase):
    def test_file_backed_param_chunking_with_rank_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targets = Path(tmpdir) / "targets.txt"
            targets.write_text("a\nb\nc\nd\n", encoding="utf-8")

            argv = [
                "runit",
                "-g",
                "0",
                "1",
                "--world_size",
                "2",
                "--rank",
                "1",
                "--target",
                f"@{targets}",
                "--",
                "echo",
                "{target}",
            ]

            with patch("sys.argv", argv):
                args, param_group, opt_group = getopt()

        self.assertEqual(args.world_size, 2)
        self.assertEqual(args.rank, 1)
        self.assertEqual(param_group["target"], ["c", "d"])
        self.assertEqual(opt_group["g"], ["0", "1"])

    def test_rank_options_after_file_backed_param_still_parse(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targets = Path(tmpdir) / "targets.txt"
            targets.write_text("a\nb\nc\nd\n", encoding="utf-8")

            argv = [
                "runit",
                "-g",
                "0",
                "1",
                "--target",
                f"@{targets}",
                "--world_size",
                "2",
                "--rank",
                "1",
                "--",
                "echo",
                "{target}",
            ]

            with patch("sys.argv", argv):
                args, param_group, opt_group = getopt()

        self.assertEqual(args.world_size, 2)
        self.assertEqual(args.rank, 1)
        self.assertEqual(param_group["target"], ["c", "d"])
        self.assertEqual(opt_group["g"], ["0", "1"])

    def test_n_threads_creates_worker_axis_without_worker_option(self):
        argv = [
            "runit",
            "-n",
            "2",
            "--item",
            "x",
            "y",
            "--",
            "echo",
            "{item}",
        ]

        with patch("sys.argv", argv):
            args, param_group, opt_group = getopt()

        self.assertEqual(args.n_threads, 2)
        self.assertEqual(param_group["item"], ["x", "y"])
        self.assertEqual(opt_group["n"], ["0", "1"])


if __name__ == "__main__":
    unittest.main()
