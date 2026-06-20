"""
CraftSplat-20 CLI 入口
======================

基于 argparse 的命令行工具，提供六个子命令：
    capture-plan, prepare, colmap, train, export, report
"""

import argparse
import sys
import os
from typing import Optional

from craftsplat import __version__

# 导入各子命令模块
from craftsplat.commands.capture_plan import register_parser as _reg_cp, run as _run_cp
from craftsplat.commands.prepare import register_parser as _reg_prep, run as _run_prep
from craftsplat.commands.colmap_cmd import register_parser as _reg_colmap, run as _run_colmap
from craftsplat.commands.train_cmd import register_parser as _reg_train, run as _run_train
from craftsplat.commands.export_cmd import register_parser as _reg_export, run as _run_export
from craftsplat.commands.report import register_parser as _reg_report, run as _run_report


def main(argv: Optional[list] = None) -> int:
    """CraftSplat-20 CLI 主入口。

    Parameters
    ----------
    argv : list, optional
        命令行参数列表，默认 sys.argv[1:]。

    Returns
    -------
    int
        退出码，0 表示成功。
    """
    parser = argparse.ArgumentParser(
        prog="craftsplat",
        description=(
            "CraftSplat-20 — 少图文创手办 3D Gaussian Splatting 建模工具链\n"
            "使用 20 张以内照片完成高保真视觉复刻。\n"
            "基于 Nerfstudio + gsplat 主线。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"craftsplat {__version__}"
    )

    subparsers = parser.add_subparsers(
        title="可用命令",
        dest="command",
        help="使用 <命令> --help 查看详细用法",
    )

    # 注册六个子命令
    _reg_cp(subparsers)
    _reg_prep(subparsers)
    _reg_colmap(subparsers)
    _reg_train(subparsers)
    _reg_export(subparsers)
    _reg_report(subparsers)

    # 解析参数
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    # 分发到对应子命令
    command_map = {
        "capture-plan": _run_cp,
        "prepare": _run_prep,
        "colmap": _run_colmap,
        "train": _run_train,
        "export": _run_export,
        "report": _run_report,
    }

    try:
        return command_map[args.command](args)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        print("   如果缺少外部依赖（如 COLMAP、Nerfstudio），请参考 README.md 安装说明。", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
