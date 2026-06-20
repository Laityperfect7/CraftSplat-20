"""
Nerfstudio 训练命令 (Wrapper)
=============================

使用 subprocess 调用 Nerfstudio 的 ns-train。
默认使用 Splatfacto 方法（基于 gsplat）。

如果 Nerfstudio 未安装，给出清晰报错和安装链接。

用法:
    craftsplat train DATA_DIR --method splatfacto --steps 15000
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SUPPORTED_METHODS = ["splatfacto", "gaussian-splatting", "nerfacto"]


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 train 子命令。"""
    parser = subparsers.add_parser(
        "train",
        help="训练 3DGS 模型（Nerfstudio wrapper）",
        description="封装 Nerfstudio 训练命令。需要已安装 nerfstudio 和 gsplat。",
    )
    parser.add_argument(
        "data_dir",
        type=str,
        help="数据目录（prepare 命令的输出目录）",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="splatfacto",
        choices=SUPPORTED_METHODS,
        help="训练方法: splatfacto (推荐) | gaussian-splatting | nerfacto。默认 splatfacto。",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=15000,
        help="训练步数，默认 15000。少图场景可适当减少至 7000-10000。",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录。默认在 data_dir 同级创建 runs/ 目录。",
    )
    parser.add_argument(
        "--viewer",
        action="store_true",
        help="启动 Nerfstudio Viewer（需要图形界面）",
    )


def _check_nerfstudio() -> bool:
    """检查 Nerfstudio 是否可用。"""
    if not shutil.which("ns-train"):
        return False
    try:
        result = subprocess.run(
            ["ns-train", "--help"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _process_data_for_nerfstudio(data_dir: Path) -> bool:
    """使用 ns-process-data 将数据转为 Nerfstudio 格式（如果需要）。"""
    # 检查是否已经是 Nerfstudio 格式
    if (data_dir / "transforms.json").exists():
        return True

    images_dir = data_dir / "images"
    if not images_dir.is_dir():
        print(f"❌ 图片目录不存在: {images_dir}", file=sys.stderr)
        return False

    if not shutil.which("ns-process-data"):
        print("⚠️  ns-process-data 不可用，尝试直接使用图片目录", file=sys.stderr)
        return True

    print("🔄 将数据转为 Nerfstudio 格式...")
    ns_data_dir = data_dir / "nerfstudio"
    ret = subprocess.run([
        "ns-process-data", "images",
        "--data", str(images_dir),
        "--output-dir", str(ns_data_dir),
    ]).returncode

    if ret != 0:
        print("⚠️  ns-process-data 失败，将尝试直接使用图片目录", file=sys.stderr)
    return True


def run(args: argparse.Namespace) -> int:
    """执行 train 命令。"""
    data_dir = Path(args.data_dir)

    # 验证
    if not data_dir.is_dir():
        print(f"❌ 数据目录不存在: {data_dir}", file=sys.stderr)
        print("   请先运行: craftsplat prepare INPUT_DIR OUTPUT_DIR", file=sys.stderr)
        return 1

    # 检查 Nerfstudio
    if not _check_nerfstudio():
        print("=" * 60)
        print("❌ Nerfstudio 未安装或不在 PATH 中")
        print("=" * 60)
        print()
        print("Nerfstudio 是训练 3DGS 模型的核心框架。")
        print()
        print("📥 安装方法:")
        print("  pip install nerfstudio")
        print()
        print("详细安装说明:")
        print("  https://docs.nerf.studio/quickstart/installation.html")
        print()
        print("⚠️  注意:")
        print("  • 需要 CUDA 环境 (NVIDIA GPU + CUDA 11.8+)")
        print("  • 推荐在 conda 环境中安装:")
        print("    conda create -n craftsplat python=3.10 -y")
        print("    conda activate craftsplat")
        print("    pip install nerfstudio")
        print("  • 安装后验证: ns-train --help")
        print()
        print(f"📝 安装完成后运行:")
        print(f"    craftsplat train {data_dir} --method {args.method} --steps {args.steps}")
        return 1

    # 预处理数据
    _process_data_for_nerfstudio(data_dir)

    # 确定数据路径
    if (data_dir / "nerfstudio" / "transforms.json").exists():
        ns_data = data_dir / "nerfstudio"
    elif (data_dir / "transforms.json").exists():
        ns_data = data_dir
    else:
        ns_data = data_dir

    # 构建训练命令
    output_dir = args.output_dir or str(data_dir / "runs")
    cmd = [
        "ns-train", args.method,
        "--data", str(ns_data),
        "--output-dir", output_dir,
        "--max-num-iterations", str(args.steps),
        "--pipeline.model.cull_alpha_thresh", "0.005",
    ]

    if not args.viewer:
        cmd.append("--viewer.quit-on-train-completion")
        cmd.append("True")

    print("=" * 60)
    print(f"🚀 开始训练: {args.method}")
    print(f"   数据:  {ns_data}")
    print(f"   步数:  {args.steps}")
    print(f"   输出:  {output_dir}")
    print("=" * 60)
    print()
    print("💡 训练过程中可以:")
    print("  • 浏览器访问 https://viewer.nerf.studio 查看实时结果")
    print("  • Ctrl+C 停止训练（已保存的 checkpoint 会保留）")
    print()

    # 执行训练
    ret = subprocess.run(cmd).returncode

    if ret != 0:
        print()
        print("❌ 训练失败", file=sys.stderr)
        print("💡 常见原因和解决方案请参见: docs/troubleshooting.md", file=sys.stderr)
        return 1

    print()
    print(f"✅ 训练完成")
    print(f"💡 下一步: craftsplat export {output_dir}")
    return 0
