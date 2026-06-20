# CraftSplat-20 Example: 潮玩手办画廊

## 场景描述

这是一个典型的文创产品扫描场景：
- **物体**: 一个 12cm 高的潮流玩具手办（哑光表面，多色涂装）
- **拍摄方式**: 18 张环绕 + 2 张顶部校准
- **光照**: 柔光箱 + 自然窗光混合
- **背景**: 浅灰色无缝背景纸
- **转盘**: 使用手动转盘，每 20° 旋转一次

## 预期输入

```
touch-gallery/
├── IMG_0001.jpg  → 方位 0°,   仰角 +30° (上环)
├── IMG_0002.jpg  → 方位 45°,  仰角 +30°
├── IMG_0003.jpg  → 方位 90°,  仰角 +30°
├── IMG_0004.jpg  → 方位 135°, 仰角 +30°
├── IMG_0005.jpg  → 方位 180°, 仰角 +30°
├── IMG_0006.jpg  → 方位 225°, 仰角 +30°
├── IMG_0007.jpg  → 方位 270°, 仰角 +30°
├── IMG_0008.jpg  → 方位 315°, 仰角 +30°
├── IMG_0009.jpg  → 方位 0°,   仰角 0°   (中环)
├── IMG_0010.jpg  → 方位 60°,  仰角 0°
├── IMG_0011.jpg  → 方位 120°, 仰角 0°
├── IMG_0012.jpg  → 方位 180°, 仰角 0°
├── IMG_0013.jpg  → 方位 240°, 仰角 0°
├── IMG_0014.jpg  → 方位 300°, 仰角 0°
├── IMG_0015.jpg  → 方位 0°,   仰角 -20° (下环)
├── IMG_0016.jpg  → 方位 90°,  仰角 -20°
├── IMG_0017.jpg  → 方位 180°, 仰角 -20°
├── IMG_0018.jpg  → 方位 270°, 仰角 -20°
├── IMG_0019.jpg  → 方位 0°,   仰角 +55° (校准)
├── IMG_0020.jpg  → 方位 180°, 仰角 +60° (校准)
```

## 运行方式

```bash
# 生成拍摄计划
craftsplat capture-plan --photos 20 --rings "8,6,4" --eval 2

# 预处理
craftsplat prepare examples/touch-gallery craft_output --max-photos 20 --resize 1600

# COLMAP
craftsplat colmap craft_output

# 训练
craftsplat train craft_output --method splatfacto --steps 10000

# 导出
craftsplat export craft_output --formats ply,splat
```

## 预期结果 (mock)

> ⚠️ 以下为示意数据，非真实训练结果。

| 指标 | 预期范围 |
|------|---------|
| PSNR | 25-35 dB (理想条件) |
| SSIM | 0.85-0.95 (理想条件) |
| 训练时间 | 30-60 分钟 (RTX 4070) |
| 导出 PLY | ~500K-2M 高斯点 |

## 注意事项

- 手办表面应为哑光或轻度光泽；高光涂装可能导致 COLMAP 匹配困难
- 拍摄间物体不可移动；转盘式拍摄优于手持环绕
- 如需 mesh，请在训练后使用 SuGaR 提取表面
