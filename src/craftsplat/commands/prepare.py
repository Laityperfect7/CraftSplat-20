"""
图片预处理命令
==============

对输入图片执行：复制、排序、resize、mask 生成。
生成 manifest.json 供后续流水线使用。

用法:
    craftsplat prepare INPUT_DIR OUTPUT_DIR --max-photos 20 --resize 1600 --mask rembg
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

# 尝试导入可选依赖
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 prepare 子命令。"""
    parser = subparsers.add_parser(
        "prepare",
        help="图片预处理：排序、resize、mask",
        description="将输入目录中的图片复制到输出目录，按名称排序，可选 resize 和 mask 生成。",
    )
    parser.add_argument(
        "input_dir",
        type=str,
        help="原始照片目录",
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="预处理输出目录",
    )
    parser.add_argument(
        "--max-photos",
        type=int,
        default=20,
        help="最大处理张数，默认 20",
    )
    parser.add_argument(
        "--resize",
        type=int,
        default=1600,
        help="长边像素数，默认 1600。0 表示不缩放。",
    )
    parser.add_argument(
        "--mask",
        type=str,
        default="none",
        choices=["none", "rembg", "colmap"],
        help="mask 生成方式: none | rembg | colmap。默认 none。"
             "rembg 需要 pip install rembg。",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="JPEG 输出质量 (1-100)，默认 95",
    )


def _collect_images(input_dir: Path) -> List[Path]:
    """收集目录中的图像文件，按名称排序。"""
    images = []
    for p in sorted(input_dir.iterdir()):
        if p.suffix.lower() in SUPPORTED_EXTS:
            images.append(p)
    return images


def _resize_image(src: Path, dst: Path, long_edge: int, quality: int) -> Tuple[int, int]:
    """缩放图像，保持比例，长边对齐。"""
    if not HAS_CV2 and not HAS_PIL:
        shutil.copy2(src, dst)
        return (0, 0)

    if HAS_CV2:
        img = cv2.imread(str(src))
        if img is None:
            shutil.copy2(src, dst)
            return (0, 0)
        h, w = img.shape[:2]
        if long_edge > 0 and max(h, w) > long_edge:
            scale = long_edge / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return (img.shape[1], img.shape[0])
    else:
        img = Image.open(src)
        w, h = img.size
        if long_edge > 0 and max(h, w) > long_edge:
            scale = long_edge / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        img.save(dst, quality=quality)
        return img.size


def _generate_mask(src: Path, dst: Path, method: str) -> bool:
    """生成前景 mask。

    Parameters
    ----------
    src : Path
        原图路径。
    dst : Path
        mask 输出路径（PNG）。
    method : str
        'rembg' 或 'colmap'。
    """
    if method == "none":
        return True

    if method == "rembg":
        try:
            from rembg import remove
            from PIL import Image
            img = Image.open(src)
            # rembg 返回 RGBA，我们取 alpha 通道作为 mask
            result = remove(img)
            if result.mode == "RGBA":
                mask = result.split()[-1]
                mask.save(dst)
            else:
                # 没有透明通道，生成全白 mask
                white = Image.new("L", img.size, 255)
                white.save(dst)
            return True
        except ImportError:
            print("  ⚠️  rembg 未安装。请运行: pip install rembg", file=sys.stderr)
            print("  跳过 mask 生成。", file=sys.stderr)
            return False
        except Exception as e:
            print(f"  ⚠️  mask 生成失败: {e}", file=sys.stderr)
            return False

    # colmap 方式：先不做，训练时由 Nerfstudio 处理
    return True


def run(args: argparse.Namespace) -> int:
    """执行 prepare 命令。"""
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # 验证输入
    if not input_dir.is_dir():
        print(f"❌ 输入目录不存在: {input_dir}", file=sys.stderr)
        return 1

    # 收集图片
    images = _collect_images(input_dir)
    if not images:
        print(f"❌ 目录中没有支持的图片文件: {input_dir}", file=sys.stderr)
        print(f"   支持格式: {', '.join(SUPPORTED_EXTS)}", file=sys.stderr)
        return 1

    print(f"📂 找到 {len(images)} 张图片")

    # 限制数量
    if len(images) > args.max_photos:
        print(f"⚠️  图片超过 {args.max_photos} 张限制，仅处理前 {args.max_photos} 张")
        images = images[:args.max_photos]

    # 创建输出目录
    images_dir = output_dir / "images"
    masks_dir = output_dir / "masks"
    images_dir.mkdir(parents=True, exist_ok=True)
    if args.mask != "none":
        masks_dir.mkdir(parents=True, exist_ok=True)

    # 处理每张图片
    manifest_entries = []
    print(f"🖼️  处理 {len(images)} 张图片...")

    for i, src_path in enumerate(images):
        stem = f"{i+1:03d}"
        dst_path = images_dir / f"{stem}.jpg"

        # Resize + 复制
        new_size = _resize_image(src_path, dst_path, args.resize, args.quality)
        w, h = new_size if new_size != (0, 0) else (0, 0)

        # Mask
        mask_path = None
        if args.mask != "none":
            mask_dst = masks_dir / f"{stem}_mask.png"
            ok = _generate_mask(src_path, mask_dst, args.mask)
            if ok:
                mask_path = str(mask_dst.relative_to(output_dir))

        entry = {
            "index": i,
            "original_name": src_path.name,
            "output_name": dst_path.name,
            "width": w,
            "height": h,
            "mask_path": mask_path,
        }
        manifest_entries.append(entry)

        if (i + 1) % 10 == 0 or i == len(images) - 1:
            print(f"  进度: {i+1}/{len(images)}")

    # 写入 manifest
    manifest = {
        "tool": "CraftSplat-20",
        "version": "0.1.0",
        "created_at": datetime.now().isoformat(),
        "input_dir": str(input_dir.resolve()),
        "output_dir": str(output_dir.resolve()),
        "num_images": len(images),
        "resize_long_edge": args.resize if args.resize > 0 else None,
        "mask_method": args.mask,
        "images": manifest_entries,
    }

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # 摘要
    print("-" * 60)
    print(f"✅ 预处理完成")
    print(f"   处理图片:  {len(images)} 张")
    print(f"   Resize:    {args.resize}px long edge" if args.resize > 0 else "   Resize:    未缩放")
    print(f"   Mask:      {args.mask}")
    print(f"   输出目录:  {output_dir}")
    print(f"   Manifest:  {manifest_path}")
    print()
    print("💡 下一步:")
    print(f"   craftsplat colmap {output_dir}")
    print(f"   craftsplat train {output_dir}")

    return 0
