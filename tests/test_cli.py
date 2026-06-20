"""
测试: CLI 入口
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from craftsplat.cli import main


class TestCLIEntry:
    """测试 CLI 入口点。"""

    def test_no_args_prints_help(self):
        """测试无参数时打印帮助并返回非零。"""
        ret = main([])
        assert ret == 1

    def test_version(self):
        """测试 --version 参数。"""
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0

    def test_subcommand_help(self):
        """测试子命令帮助（--help 会触发 sys.exit(0)）。"""
        # capture-plan --help
        with pytest.raises(SystemExit) as exc:
            main(["capture-plan", "--help"])
        assert exc.value.code == 0

        # prepare --help
        with pytest.raises(SystemExit) as exc:
            main(["prepare", "--help"])
        assert exc.value.code == 0

    def test_invalid_subcommand(self):
        """测试无效子命令。"""
        with pytest.raises(SystemExit) as exc:
            main(["invalid-command"])
        assert exc.value.code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
