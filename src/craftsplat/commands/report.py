"""
运行报告生成命令
================

从运行目录收集信息，生成结构化的 Markdown 报告。

用法:
    craftsplat report RUN_DIR --eval-dir EVAL_DIR
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 report 子命令。"""
    parser = subparsers.add_parser(
        "report",
        help="生成运行报告",
        description="从运行目录生成 Markdown 格式的运行报告。",
    )
    parser.add_argument(
        "run_dir",
        type=str,
        help="训练运行目录",
    )
    parser.add_argument(
        "--eval-dir",
        type=str,
        default=None,
        help="评估图像目录（可选）",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出报告路径。默认为 run_dir/report.md",
    )


def _count_files(directory: Path, extensions: set) -> int:
    """统计目录中特定扩展名的文件数量。"""
    if not directory.is_dir():
        return 0
    count = 0
    for p in directory.iterdir():
        if p.suffix.lower() in extensions:
            count += 1
    return count


def _get_resolution_stats(images_dir: Path) -> dict:
    """获取图像分辨率统计。"""
    if not images_dir.is_dir():
        return {"count": 0, "resolutions": []}

    try:
        from PIL import Image
        resolutions = []
        for p in sorted(images_dir.iterdir()):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                try:
                    img = Image.open(p)
                    resolutions.append(f"{img.width}x{img.height}")
                except Exception:
                    pass
        return {
            "count": len(resolutions),
            "resolutions": list(set(resolutions)),
        }
    except ImportError:
        return {"count": _count_files(images_dir, {".jpg", ".jpeg", ".png"}), "resolutions": ["unknown"]}


def _find_checkpoint(run_dir: Path) -> Optional[str]:
    """查找 checkpoint 文件。"""
    for pattern in ["**/checkpoint.pt", "**/*.ckpt", "**/point_cloud.ply"]:
        candidates = list(run_dir.glob(pattern))
        if candidates:
            return str(candidates[0].relative_to(run_dir))
    return None


def run(args: argparse.Namespace) -> int:
    """执行 report 命令。"""
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"❌ 运行目录不存在: {run_dir}", file=sys.stderr)
        return 1

    # 收集信息
    output_path = Path(args.output) if args.output else run_dir / "report.md"

    images_dir = run_dir / "images"
    manifest_path = run_dir / "manifest.json"

    # 读取 manifest
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

    image_count = manifest.get("num_images", _count_files(images_dir, {".jpg", ".jpeg", ".png"}))
    resolution_info = _get_resolution_stats(images_dir)
    checkpoint = _find_checkpoint(run_dir)
    eval_count = 0
    if args.eval_dir:
        eval_count = _count_files(Path(args.eval_dir), {".jpg", ".jpeg", ".png"})

    # 生成报告
    report_lines = [
        f"# CraftSplat-20 运行报告",
        "",
        f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**项目版本:** 0.1.0",
        "",
        "---",
        "",
        "## 运行概览",
        "",
        f"| 项目 | 值 |",
        f"|------|----|",
        f"| 运行目录 | `{run_dir}` |",
        f"| 训练图片数 | {image_count} |",
        f"| 评估图片数 | {eval_count if args.eval_dir else 'N/A'} |",
        f"| 图片分辨率 | {', '.join(resolution_info['resolutions'])} |",
        f"| Checkpoint | `{checkpoint or '未找到'}` |",
        "",
        "## 图片详情",
        "",
    ]

    if manifest and "images" in manifest:
        report_lines.append("| # | 原始文件名 | 输出文件名 | 分辨率 | Mask |")
        report_lines.append("|---|-----------|-----------|--------|------|")
        for img in manifest["images"]:
            mask = "✅" if img.get("mask_path") else "—"
            report_lines.append(
                f"| {img['index']+1} | {img['original_name']} | "
                f"{img['output_name']} | {img['width']}x{img['height']} | {mask} |"
            )

    report_lines += [
        "",
        "## 质量指标（占位）",
        "",
        "> ⚠️ 以下指标为占位值。运行真实评估后替换为实际数值。",
        "",
        "| 指标 | 值 | 说明 |",
        "|------|----|------|",
        "| PSNR | TBD | 峰值信噪比 |",
        "| SSIM | TBD | 结构相似性 |",
        "| LPIPS | TBD | 感知相似度 |",
        "| 训练时间 | TBD | 实际训练用时 |",
        "| GPU 显存峰值 | TBD | VRAM 使用峰值 |",
        "",
        "## 命令记录",
        "",
        "请在此记录实际运行的命令：",
        "",
        "```bash",
        "# 预处理",
        f"# craftsplat prepare <INPUT> {run_dir} --max-photos 20 --resize 1600",
        "",
        "# COLMAP",
        f"# craftsplat colmap {run_dir} --matcher exhaustive",
        "",
        "# 训练",
        f"# craftsplat train {run_dir} --method splatfacto --steps 15000",
        "",
        "# 导出",
        f"# craftsplat export {run_dir} --formats ply,splat",
        "```",
        "",
        "## 评估结果（占位）",
        "",
        "> 运行 `craftsplat train` 并在评估集上计算指标后，此处将填充真实数值。",
        "",
        "## 备注",
        "",
        "- 本报告由 CraftSplat-20 自动生成",
        "- 真实质量指标需运行标准评估脚本获得",
        "- 如需 mesh 导出，请参考 `docs/pipeline.md`",
    ]

    report_text = "\n".join(report_lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print("=" * 60)
    print(f"📋 运行报告已生成")
    print(f"   报告: {output_path}")
    print(f"   图片数: {image_count}")
    print(f"   分辨率: {', '.join(resolution_info['resolutions'])}")
    print(f"   Checkpoint: {checkpoint or '未找到'}")
    print()
    print("💡 质量指标目前为占位值。运行真实评估后更新。")

    return 0
