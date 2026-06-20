# CraftSplat-20 Example: 手工陶瓷杯

## 场景描述

手工制作的陶瓷咖啡杯，具有：
- 有机不规则外形（手工痕迹）
- 哑光釉面，局部有纹理
- 高约 10cm，最宽处约 8cm

## 拍摄方式

- 使用 12 张环绕照片（单环，仰角轻微变化）
- 相机：手机主摄（等效 26mm）
- 转盘：手动旋转，每 30° 一张
- 标尺：旁边放置 10cm 参照物用于尺度标定

## 运行方式

```bash
craftsplat prepare examples/handmade-ceramic craft_output --max-photos 12 --resize 1600
craftsplat colmap craft_output
craftsplat train craft_output --method splatfacto --steps 7000
craftsplat export craft_output --formats ply,splat
```

## 对 3DGS 友好的物体特征

此陶瓷杯适合 3DGS 建模，因为：
- ✅ 表面有足够的纹理（釉面微纹理、手工痕跡）
- ✅ 外形不透明（无半透明区域）
- ✅ 没有镜面高光
- ✅ 有机形态（比几何精确的 CAD 件更适合点云表示）

## 不适用场景参考

如果物体有以下特征，效果可能不佳：
- ❌ 完全光滑无纹理的白色瓷面
- ❌ 镜面/镀铬光泽
- ❌ 透明玻璃材质
- ❌ 极细线状结构（如首饰链条）
