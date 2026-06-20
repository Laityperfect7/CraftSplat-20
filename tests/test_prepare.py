"""
测试: prepare 命令
"""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from craftsplat.commands.prepare import run, _collect_images, SUPPORTED_EXTS


class TestPrepareCommand:
    """测试 prepare 命令。"""

    def _create_test_images(self, directory, count=5):
        """创建测试图像文件。"""
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        for i in range(count):
            img = Image.new("RGB", (400, 300), color=(i * 50, 100, 150))
            img.save(os.path.join(directory, f"img_{i:03d}.jpg"))

    def test_empty_directory(self):
        """测试空目录报错。"""
        import argparse
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "empty")
            os.makedirs(input_dir)
            output_dir = os.path.join(tmpdir, "out")

            args = argparse.Namespace(
                input_dir=input_dir,
                output_dir=output_dir,
                max_photos=20,
                resize=1600,
                mask="none",
                quality=95,
            )
            ret = run(args)
            # 应该返回非零（没有图片）
            assert ret != 0

    def test_basic_prepare(self):
        """测试基本预处理。"""
        import argparse
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "input")
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(input_dir)

            self._create_test_images(input_dir, 5)

            args = argparse.Namespace(
                input_dir=input_dir,
                output_dir=output_dir,
                max_photos=20,
                resize=0,
                mask="none",
                quality=95,
            )
            ret = run(args)
            assert ret == 0

            # 检查输出
            assert os.path.exists(os.path.join(output_dir, "manifest.json"))
            assert os.path.isdir(os.path.join(output_dir, "images"))

            # 检查 manifest
            with open(os.path.join(output_dir, "manifest.json"), "r") as f:
                manifest = json.load(f)
            assert manifest["num_images"] == 5
            assert len(manifest["images"]) == 5

            # 检查图片文件
            images_dir = os.path.join(output_dir, "images")
            image_files = os.listdir(images_dir)
            assert len(image_files) == 5

    def test_max_photos_limit(self):
        """测试 max_photos 限制。"""
        import argparse
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "input")
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(input_dir)

            self._create_test_images(input_dir, 10)

            args = argparse.Namespace(
                input_dir=input_dir,
                output_dir=output_dir,
                max_photos=3,
                resize=0,
                mask="none",
                quality=95,
            )
            ret = run(args)
            assert ret == 0

            with open(os.path.join(output_dir, "manifest.json"), "r") as f:
                manifest = json.load(f)
            assert manifest["num_images"] == 3

    def test_nonexistent_input(self):
        """测试不存在的输入目录。"""
        import argparse
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                input_dir="/nonexistent/path/xyz",
                output_dir=os.path.join(tmpdir, "out"),
                max_photos=20,
                resize=1600,
                mask="none",
                quality=95,
            )
            ret = run(args)
            assert ret != 0


class TestCollectImages:
    """测试图片收集。"""

    def test_collect_images(self):
        """测试收集指定扩展名的图片。"""
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            for ext in [".jpg", ".png", ".bmp"]:
                (d / f"test{ext}").touch()
            # 非图片文件
            (d / "test.txt").touch()

            images = _collect_images(d)
            assert len(images) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
