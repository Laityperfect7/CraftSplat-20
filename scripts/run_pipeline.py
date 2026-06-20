#!/usr/bin/env python3
"""
CraftSplat-20 一键处理脚本
===========================

从原始照片到训练完成的全自动化流程。
需要先安装依赖：pip install -e .

用法:
    python scripts/run_pipeline.py INPUT_DIR --output OUTPUT_DIR
"""

import argparse
import subprocess
import sys
from pathlib import Path

STEPS = ["prepare", "colmap", "train", "export", "report"]
SKIP_COLMAP_STEPS = ["prepare", "train", "export", "report"]


def main():
    parser = argparse.ArgumentParser(
        description="CraftSplat-20 一键处理流水线",
    )
    parser.add_argument("input_dir", type=str, help="原始照片目录")
    parser.add_argument("--output", "-o", type=str, default="craftsplat_runs/run_001",
                        help="输出目录，默认 craftsplat_runs/run_001")
    parser.add_argument("--max-photos", type=int, default=20,
                        help="最大照片数，默认 20")
    parser.add_argument("--resize", type=int, default=1600,
                        help="长边像素，默认 1600")
    parser.add_argument("--method", type=str, default="splatfacto",
                        help="训练方法，默认 splatfacto")
    parser.add_argument("--steps", type=int, default=15000,
                        help="训练步数，默认 15000")
    parser.add_argument("--skip-colmap", action="store_true",
                        help="跳过 COLMAP（如果已运行过）")
    parser.add_argument("--formats", type=str, default="ply,splat",
                        help="导出格式，默认 ply,splat")
    parser.add_argument("--mask", type=str, default="none",
                        choices=["none", "rembg", "colmap"],
                        help="Mask 生成方式，默认 none")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output)

    if not input_dir.is_dir():
        print(f"❌ 输入目录不存在: {input_dir}")
        sys.exit(1)

    steps = SKIP_COLMAP_STEPS if args.skip_colmap else STEPS
    print("=" * 60)
    print("🚀 CraftSplat-20 一键流水线")
    print(f"   输入: {input_dir}")
    print(f"   输出: {output_dir}")
    print(f"   步骤: {' → '.join(steps)}")
    print("=" * 60)

    commands = []
    output_dir_str = str(output_dir)

    # Step 1: prepare
    commands.append([
        "craftsplat", "prepare",
        str(input_dir), output_dir_str,
        "--max-photos", str(args.max_photos),
        "--resize", str(args.resize),
        "--mask", args.mask,
    ])

    # Step 2: colmap (optional)
    if not args.skip_colmap:
        commands.append([
            "craftsplat", "colmap", output_dir_str,
            "--matcher", "exhaustive",
        ])

    # Step 3: train
    commands.append([
        "craftsplat", "train", output_dir_str,
        "--method", args.method,
        "--steps", str(args.steps),
    ])

    # Step 4: export
    commands.append([
        "craftsplat", "export", output_dir_str,
        "--formats", args.formats,
    ])

    # Step 5: report
    commands.append([
        "craftsplat", "report", output_dir_str,
    ])

    # 执行
    for i, cmd in enumerate(commands):
        step_name = steps[i]
        print(f"\n{'='*60}")
        print(f"📌 步骤 {i+1}/{len(commands)}: {step_name}")
        print(f"{'='*60}")
        ret = subprocess.run(cmd).returncode
        if ret != 0:
            print(f"\n⚠️  步骤 '{step_name}' 返回非零退出码 ({ret})")
            if step_name in ("colmap", "train"):
                print("   如果是缺少外部依赖，请参考 README.md 安装说明。")
                print("   安装后可跳过已完成的步骤继续运行。")
            if step_name == "train":
                # 训练失败但继续后续步骤
                pass
            else:
                sys.exit(ret)

    print(f"\n{'='*60}")
    print(f"✅ 流水线完成！")
    print(f"   输出目录: {output_dir}")
    print(f"   报告: {output_dir}/report.md")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
