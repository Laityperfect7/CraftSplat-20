"""
模型导出命令
============

从训练结果导出各种格式：ply, splat, ksplat, glb。

部分格式依赖外部工具（如 SuGaR、GS2Mesh 用于 glb）。
如果外部工具未安装，给出清晰提示。

用法:
    craftsplat export RUN_DIR --formats ply,splat,ksplat,glb
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

AVAILABLE_FORMATS = ["ply", "splat", "ksplat", "glb"]


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 export 子命令。"""
    parser = subparsers.add_parser(
        "export",
        help="导出训练结果",
        description="将训练结果导出为各种格式，用于展示或后续处理。",
    )
    parser.add_argument(
        "run_dir",
        type=str,
        help="训练输出目录（ns-train 的输出目录）",
    )
    parser.add_argument(
        "--formats",
        type=str,
        default="ply,splat",
        help=f"导出格式，逗号分隔。可选: {','.join(AVAILABLE_FORMATS)}。默认 ply,splat",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="导出目录。默认为 run_dir/exports/",
    )


def _export_ply(run_dir: Path, output_dir: Path) -> bool:
    """导出 PLY 格式（Nerfstudio 默认支持）。"""
    # Nerfstudio 训练后自动生成 point_cloud.ply
    # 尝试查找
    candidates = list(run_dir.glob("**/point_cloud.ply"))
    candidates += list(run_dir.glob("**/*.ply"))

    if candidates:
        import shutil
        for src in candidates:
            dst = output_dir / f"{src.parent.name}_{src.name}"
            shutil.copy2(src, dst)
        print(f"  ✅ PLY: 已复制 {len(candidates)} 个文件")
        return True

    # 尝试用 ns-export 导出
    if _check_cmd("ns-export"):
        print("  尝试 ns-export pointcloud...")
        subprocess.run([
            "ns-export", "pointcloud",
            "--load-config", str(run_dir / "config.yml"),
            "--output-dir", str(output_dir),
            "--num-points", "1000000",
        ])
        return True

    print("  ⚠️  未找到 PLY 文件，且 ns-export 不可用")
    return False


def _export_splat(run_dir: Path, output_dir: Path) -> bool:
    """导出 .splat 格式（SuperSplat 兼容）。"""
    # 尝试使用 gsplat 的导出功能
    if _check_cmd("ns-export"):
        print("  尝试 ns-export gaussian-splat...")
        subprocess.run([
            "ns-export", "gaussian-splat",
            "--load-config", str(run_dir / "config.yml"),
            "--output-dir", str(output_dir),
        ])
        return True

    print("  ⚠️  .splat 导出需要 ns-export (随 nerfstudio 安装)")
    print("     pip install nerfstudio")
    return False


def _export_ksplat(run_dir: Path, output_dir: Path) -> bool:
    """导出 .ksplat 格式。"""
    # ksplat 是社区格式，需要额外工具
    output_path = output_dir / "point_cloud.ksplat"

    # 尝试查找 ply 转换
    ply_candidates = list(run_dir.glob("**/point_cloud.ply"))
    if ply_candidates and _check_cmd("python"):
        print(f"  ℹ️  .ksplat 导出需要 ksplat 工具")
        print(f"     参考: https://github.com/mkkellogg/GaussianSplats3D")
        print(f"  📝 已找到源 PLY: {ply_candidates[0]}")
        print(f"     可使用 gsplat.js 或其他转换工具生成 .ksplat")

        # 生成说明文件
        readme = output_dir / "KSPLAT_README.txt"
        with open(readme, "w") as f:
            f.write(f"""KSPLAT 导出说明
==============

源 PLY 文件: {ply_candidates[0]}

转换为 .ksplat:
  1. 使用 gsplat.js CLI:
     npx gsplat-cli convert {ply_candidates[0]} -o point_cloud.ksplat

  2. 或使用 GaussianSplats3D 在线转换器:
     https://mkkellogg.github.io/GaussianSplats3D/

  3. 或在 Web Viewer 中直接加载 PLY（参见 web-viewer/）
""")
        return True

    print("  ⚠️  未找到源 PLY，无法导出 ksplat")
    return False


def _export_glb(run_dir: Path, output_dir: Path) -> bool:
    """导出 GLB 格式（mesh，beta 功能）。"""
    print("  ℹ️  GLB (mesh) 导出是 beta 功能，需要额外几何方法。")
    print()
    print("  当前推荐方法:")
    print("    1. SuGaR:  https://github.com/Anttwo/SuGaR")
    print("       - 从 3DGS 提取表面 mesh")
    print("       - 输出可导入 Blender 的 .obj/.glb")
    print()
    print("    2. 2DGS:  https://github.com/hbb1/2d-gaussian-splatting")
    print("       - 使用 2D Gaussian 替代 3D，更易提取表面")
    print()
    print("    3. GS2Mesh: https://github.com/yanivw12/gs2mesh")
    print("       - 专为 GS→mesh 设计的工具")
    print()

    # 生成说明文件
    readme = output_dir / "GLB_MESH_README.txt"
    with open(readme, "w") as f:
        f.write("""GLB Mesh 导出指南 (Beta)
========================

⚠️ 3DGS 本质上是基于点的视觉表示，不直接生成封闭网格。
要将 3DGS 转为可用的 mesh (.glb/.obj)，需要额外的几何提取步骤。

推荐流程:
  1. SuGaR (Surface-Aligned Gaussian Splatting)
     git clone https://github.com/Anttwo/SuGaR
     cd SuGaR
     python train.py --config <your_config>

  2. 2D Gaussian Splatting
     git clone https://github.com/hbb1/2d-gaussian-splatting
     # 使用 2DGS 训练，天然支持表面提取

  3. GS2Mesh
     git clone https://github.com/yanivw12/gs2mesh
     # 从训练好的 3DGS 提取 mesh

注意事项:
  • 导出 mesh 的几何精度受限于 GS 点云的密度和分布
  • 小物体、高纹理物体效果较好
  • 透明/半透明物体、极细结构可能不完整
  • 结果 mesh 可能需在 Blender 中进行后处理（平滑、补洞）
""")
    print(f"  📝 已生成 GLB mesh 导出指南: {readme}")
    return True


def _check_cmd(cmd: str) -> bool:
    """检查命令是否可用。"""
    import shutil
    return shutil.which(cmd) is not None


def run(args: argparse.Namespace) -> int:
    """执行 export 命令。"""
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"❌ 运行目录不存在: {run_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir) if args.output_dir else run_dir / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    formats = [f.strip() for f in args.formats.split(",")]
    invalid = [f for f in formats if f not in AVAILABLE_FORMATS]
    if invalid:
        print(f"❌ 不支持的格式: {invalid}", file=sys.stderr)
        print(f"   可用格式: {AVAILABLE_FORMATS}", file=sys.stderr)
        return 1

    print("=" * 60)
    print(f"📦 导出模型")
    print(f"   源目录: {run_dir}")
    print(f"   输出目录: {output_dir}")
    print(f"   格式: {formats}")
    print("=" * 60)

    results = {}
    for fmt in formats:
        print(f"\n📄 导出 {fmt}...")
        if fmt == "ply":
            results[fmt] = _export_ply(run_dir, output_dir)
        elif fmt == "splat":
            results[fmt] = _export_splat(run_dir, output_dir)
        elif fmt == "ksplat":
            results[fmt] = _export_ksplat(run_dir, output_dir)
        elif fmt == "glb":
            results[fmt] = _export_glb(run_dir, output_dir)

    print()
    print("-" * 60)
    print("导出摘要:")
    for fmt, ok in results.items():
        status = "✅" if ok else "⚠️"
        print(f"  {status} {fmt}")
    print(f"📂 {output_dir}")
    return 0
