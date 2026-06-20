"""
COLMAP Wrapper 命令
===================

封装 COLMAP 命令行，使用 subprocess 调用外部 COLMAP。
如果 COLMAP 未安装，给出清晰报错和安装链接。

用法:
    craftsplat colmap DATA_DIR --matcher exhaustive --use-masks
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 colmap 子命令。"""
    parser = subparsers.add_parser(
        "colmap",
        help="运行 COLMAP 稀疏重建（wrapper）",
        description="封装 COLMAP 进行稀疏重建。需要系统已安装 COLMAP 命令行工具。",
    )
    parser.add_argument(
        "data_dir",
        type=str,
        help="数据目录（prepare 命令的输出目录）",
    )
    parser.add_argument(
        "--matcher",
        type=str,
        default="exhaustive",
        choices=["exhaustive", "sequential", "vocab_tree", "spatial"],
        help="特征匹配策略，默认 exhaustive（少于50张推荐）",
    )
    parser.add_argument(
        "--use-masks",
        action="store_true",
        help="使用 masks/ 目录中的 mask 文件",
    )
    parser.add_argument(
        "--quality",
        type=str,
        default="high",
        choices=["low", "medium", "high", "extreme"],
        help="COLMAP 质量预设",
    )


def _find_colmap() -> str:
    """查找 COLMAP 可执行文件路径。

    Returns
    -------
    str
        'colmap' 命令名。
    """
    # 尝试常见名称
    for name in ["colmap", "COLMAP"]:
        if shutil.which(name):
            return name
    return "colmap"


def _check_colmap() -> bool:
    """检查 COLMAP 是否可用。"""
    exe = _find_colmap()
    try:
        result = subprocess.run([exe, "--help"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run(args: argparse.Namespace) -> int:
    """执行 colmap 命令。"""
    data_dir = Path(args.data_dir)
    images_dir = data_dir / "images"

    # 验证
    if not images_dir.is_dir():
        print(f"❌ 图片目录不存在: {images_dir}", file=sys.stderr)
        print("   请先运行: craftsplat prepare INPUT_DIR OUTPUT_DIR", file=sys.stderr)
        return 1

    # 检查 COLMAP
    if not _check_colmap():
        colmap_exe = _find_colmap()
        print("=" * 60)
        print("❌ COLMAP 未安装或不在 PATH 中")
        print("=" * 60)
        print()
        print("COLMAP 是 Structure-from-Motion 工具，用于计算相机位姿。")
        print()
        print("📥 安装方法:")
        print("  • Windows: 下载预编译版本")
        print("    https://colmap.github.io/install.html")
        print("  • macOS: brew install colmap")
        print("  • Linux: sudo apt install colmap")
        print("  • 或通过 conda: conda install -c conda-forge colmap")
        print()
        print("💡 也可以使用 Nerfstudio 内置的 COLMAP 处理:")
        print("    ns-process-data images --data {} --output-dir {}".format(
            str(data_dir), str(data_dir / "nerfstudio")))

        # 仍然输出一个手动运行脚本
        script_path = data_dir / "run_colmap.sh"
        with open(script_path, "w") as f:
            f.write(f"""#!/bin/bash
# CraftSplat-20: 手动运行 COLMAP
# 请确保已安装 COLMAP 并将 colmap 加入 PATH

DATA_DIR="{data_dir.resolve()}"
IMAGES_DIR="$DATA_DIR/images"
DATABASE="$DATA_DIR/database.db"
SPARSE_DIR="$DATA_DIR/sparse"

# 特征提取
colmap feature_extractor \\
  --database_path "$DATABASE" \\
  --image_path "$IMAGES_DIR" \\
  --ImageReader.camera_model SIMPLE_PINHOLE \\
  --SiftExtraction.max_image_size {2000 if args.quality == "high" else 1600}

# 特征匹配
colmap {args.matcher}_matcher \\
  --database_path "$DATABASE" \\
  --SiftMatching.guided_matching true \\
  --SiftMatching.max_num_matches 32768

# 稀疏重建
mkdir -p "$SPARSE_DIR"
colmap mapper \\
  --database_path "$DATABASE" \\
  --image_path "$IMAGES_DIR" \\
  --output_path "$SPARSE_DIR"

echo "COLMAP 完成！"
echo "运行: craftsplat train {data_dir}"
""")
        os.chmod(script_path, 0o755)
        print()
        print(f"📝 已生成手动运行脚本: {script_path}")
        print("   安装 COLMAP 后可直接运行该脚本。")
        return 1

    # COLMAP 已安装，执行重建
    colmap_exe = _find_colmap()
    database = str(data_dir / "database.db")
    sparse_dir = str(data_dir / "sparse")

    print("🔍 COLMAP 特征提取...")
    ret1 = subprocess.run([
        colmap_exe, "feature_extractor",
        "--database_path", database,
        "--image_path", str(images_dir),
        "--ImageReader.camera_model", "SIMPLE_PINHOLE",
    ]).returncode

    if ret1 != 0:
        print("❌ 特征提取失败", file=sys.stderr)
        return 1

    print("🔗 COLMAP 特征匹配...")
    ret2 = subprocess.run([
        colmap_exe, f"{args.matcher}_matcher",
        "--database_path", database,
    ]).returncode

    if ret2 != 0:
        print("❌ 特征匹配失败", file=sys.stderr)
        return 1

    print("📐 COLMAP 稀疏重建...")
    os.makedirs(sparse_dir, exist_ok=True)
    ret3 = subprocess.run([
        colmap_exe, "mapper",
        "--database_path", database,
        "--image_path", str(images_dir),
        "--output_path", sparse_dir,
    ]).returncode

    if ret3 != 0:
        print("❌ 稀疏重建失败", file=sys.stderr)
        print("💡 常见原因和解决方案请参见: docs/troubleshooting.md", file=sys.stderr)
        return 1

    print(f"✅ COLMAP 完成 → {sparse_dir}")
    print(f"💡 下一步: craftsplat train {data_dir}")
    return 0
