"""
拍摄计划生成命令
================

根据"18 张环绕 + 2 张校准"的协议，
输出推荐的拍摄角度表。

用法:
    craftsplat capture-plan --photos 20 --rings "8,6,4" --eval 2
"""

import argparse
import json
import math
from pathlib import Path

RING_DEFAULTS = "8,6,4"  # 上环 8 张 / 中环 6 张 / 下环 4 张
DEFAULT_PHOTOS = 20
DEFAULT_EVAL = 2
DEFAULT_OUTPUT = "capture_plan.json"


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 capture-plan 子命令。"""
    parser = subparsers.add_parser(
        "capture-plan",
        help="生成拍摄角度表（18+2 协议）",
        description="生成 20 张以内的多环拍摄角度表，适用于文创手办/小摆件的环绕拍摄。",
    )
    parser.add_argument(
        "--photos",
        type=int,
        default=DEFAULT_PHOTOS,
        help=f"总照片数（含评估/校准张数），默认 {DEFAULT_PHOTOS}",
    )
    parser.add_argument(
        "--rings",
        type=str,
        default=RING_DEFAULTS,
        help="各环照片数，逗号分隔，从上到下。默认 '8,6,4'",
    )
    parser.add_argument(
        "--eval",
        type=int,
        default=DEFAULT_EVAL,
        help="校准/评估视角数量，默认 2（从顶部或侧上方）。",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=DEFAULT_OUTPUT,
        help="输出 JSON 文件路径",
    )


def _generate_ring_angles(num: int, elevation_deg: float, start_azimuth: float = 0.0) -> list:
    """生成单个环的角度列表。

    Parameters
    ----------
    num : int
        该环的相机数量。
    elevation_deg : float
        仰角（度），水平为 0°，上方为正。
    start_azimuth : float
        起始方位角偏移（度）。

    Returns
    -------
    list of dict
        每个元素包含 azimuth、elevation、ring 标签。
    """
    angles = []
    for i in range(num):
        azimuth = start_azimuth + 360.0 * i / num
        angles.append({
            "index": i + 1,
            "azimuth_deg": round(azimuth % 360, 1),
            "elevation_deg": round(elevation_deg, 1),
            "ring": f"elev_{elevation_deg}",
        })
    return angles


def _generate_eval_angles(num: int) -> list:
    """生成评估/校准视角（通常从顶部或斜上方）。

    Parameters
    ----------
    num : int
        评估视角数量。

    Returns
    -------
    list of dict
    """
    angles = []
    for i in range(num):
        azimuth = i * 360.0 / num
        angles.append({
            "index": i + 1,
            "azimuth_deg": round(azimuth, 1),
            "elevation_deg": round(55.0 + i * 15.0, 1),
            "ring": "eval",
            "note": "校准/评估视角，不参与训练（可选）",
        })
    return angles


def run(args: argparse.Namespace) -> int:
    """执行 capture-plan 命令。"""
    # 解析环配置
    ring_counts = [int(x.strip()) for x in args.rings.split(",")]
    total_ring = sum(ring_counts)

    # 常用仰角配置
    # 上环：~30° 俯角 → elevation +30°
    # 中环：~0° 水平 → elevation 0°
    # 下环：~-20° 仰角 → elevation -20°
    default_elevations = [30.0, 0.0, -20.0]

    if len(ring_counts) > len(default_elevations):
        print(f"⚠️  当前最多支持 {len(default_elevations)} 层环，"
              f"已截取前 {len(default_elevations)} 个")
        ring_counts = ring_counts[:len(default_elevations)]

    # 生成各环角度
    all_angles = []
    idx_offset = 0
    for ri, count in enumerate(ring_counts):
        elev = default_elevations[ri]
        # 各环间错开起始方位角，避免垂直对齐
        stagger = ri * 15.0
        ring_angles = _generate_ring_angles(count, elev, start_azimuth=stagger)
        for a in ring_angles:
            a["index"] = idx_offset + a["index"]
        all_angles.extend(ring_angles)
        idx_offset += count

    # 生成评估角度
    eval_angles = _generate_eval_angles(args.eval)
    for a in eval_angles:
        a["index"] = idx_offset + a["index"]
    all_angles.extend(eval_angles)

    total = len(all_angles)

    # 构建输出
    plan = {
        "title": "CraftSplat-20 拍摄计划",
        "description": (
            f"环绕拍摄协议：{len(ring_counts)} 层环绕环 + "
            f"{args.eval} 张评估/校准视角，总计 {total} 张。"
        ),
        "total_photos": total,
        "total_training_photos": total - args.eval,
        "rings": [
            {"elevation_deg": default_elevations[ri], "count": ring_counts[ri]}
            for ri in range(len(ring_counts))
        ],
        "eval_count": args.eval,
        "angles": all_angles,
        "tips": [
            "使用三脚架或稳定手持，保持相机高度一致",
            "每张照片之间物体姿态不变（拍摄静物）",
            "使用柔和均匀光，避免强烈阴影和反光",
            "背景使用纯色或离物体足够远以产生自然景深分离",
            "拍摄前用清洁布擦拭镜头",
            "如需尺度参照，可在物体旁放置已知尺寸的标定物（尺子/棋盘格）",
        ],
    }

    # 输出
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    # 美化的命令行输出
    print("=" * 60)
    print(f"📸 CraftSplat-20 拍摄计划")
    print("=" * 60)
    print(f"总照片数:        {total}")
    print(f"训练照片数:      {total - args.eval}")
    print(f"评估照片数:      {args.eval}")
    print(f"环层数:          {len(ring_counts)}")
    for ri, count in enumerate(ring_counts):
        print(f"  环 {ri+1}: {count} 张 @ 仰角 {default_elevations[ri]:+.0f}°")
    print("-" * 60)
    print("详细角度表:")
    for a in all_angles:
        tag = " 📍" if a.get("ring") == "eval" else ""
        print(f"  #{a['index']:2d}  方位 {a['azimuth_deg']:6.1f}°  "
              f"仰角 {a['elevation_deg']:+6.1f}°  [{a['ring']}]{tag}")
    print("-" * 60)
    print(f"✅ 计划已保存到: {output_path}")
    print()
    print("💡 提示：")
    for tip in plan["tips"]:
        print(f"  • {tip}")

    return 0
