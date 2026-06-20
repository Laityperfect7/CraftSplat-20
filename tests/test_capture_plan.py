"""
测试: capture-plan 命令
"""

import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from craftsplat.commands.capture_plan import run, _generate_ring_angles


class TestRingAngles:
    """测试环角度生成。"""

    def test_single_ring(self):
        """测试单环生成。"""
        angles = _generate_ring_angles(8, elevation_deg=30.0)
        assert len(angles) == 8
        # 方位角应该是对称的
        azimuths = [a["azimuth_deg"] for a in angles]
        assert azimuths[0] == 0.0
        assert abs(azimuths[4] - 180.0) < 0.1

    def test_ring_with_stagger(self):
        """测试带偏移的环。"""
        angles = _generate_ring_angles(6, elevation_deg=0.0, start_azimuth=15.0)
        assert len(angles) == 6
        assert angles[0]["azimuth_deg"] == 15.0

    def test_all_elevations_correct(self):
        """测试仰角值。"""
        for elev in [30.0, 0.0, -20.0]:
            angles = _generate_ring_angles(4, elevation_deg=elev)
            for a in angles:
                assert a["elevation_deg"] == elev


class TestCapturePlanCommand:
    """测试 capture-plan 命令完整流程。"""

    def test_basic_run(self):
        """测试基本运行：默认参数。"""
        import argparse

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "plan.json")
            args = argparse.Namespace(
                photos=20,
                rings="8,6,4",
                eval=2,
                output=output_path,
            )
            ret = run(args)
            assert ret == 0
            assert os.path.exists(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
            assert plan["total_photos"] == 20
            assert plan["total_training_photos"] == 18
            assert len(plan["angles"]) == 20
            assert len(plan["rings"]) == 3
            assert plan["rings"][0]["count"] == 8
            assert plan["rings"][1]["count"] == 6
            assert plan["rings"][2]["count"] == 4

    def test_custom_rings(self):
        """测试自定义环配置。"""
        import argparse

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "plan.json")
            args = argparse.Namespace(
                photos=14,
                rings="6,4,2",
                eval=2,
                output=output_path,
            )
            ret = run(args)
            assert ret == 0

            with open(output_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
            assert plan["total_photos"] == 14
            assert len(plan["angles"]) == 14

    def test_no_eval(self):
        """测试无评估视角。"""
        import argparse

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "plan.json")
            args = argparse.Namespace(
                photos=18,
                rings="8,6,4",
                eval=0,
                output=output_path,
            )
            ret = run(args)
            assert ret == 0

            with open(output_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
            assert plan["total_photos"] == 18
            assert plan["eval_count"] == 0
            # 不应有 ring=="eval" 的点
            eval_angles = [a for a in plan["angles"] if a["ring"] == "eval"]
            assert len(eval_angles) == 0

    def test_single_ring_config(self):
        """测试单环配置。"""
        import argparse

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "plan.json")
            args = argparse.Namespace(
                photos=12,
                rings="10",
                eval=2,
                output=output_path,
            )
            ret = run(args)
            assert ret == 0

            with open(output_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
            assert plan["total_photos"] == 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
