# 完整技术流程

> CraftSplat-20 的技术管线说明，从拍摄到最终展示的完整流程。

---

## 总览

```
拍摄照片 (18+2) → 预处理 → COLMAP 位姿估计 → Nerfstudio 训练 → 导出 → 展示
```

---

## 第一步：照片采集

详见 [拍摄指南](capture_guide_zh.md)。

```bash
# 生成拍摄计划
craftsplat capture-plan --photos 20 --rings "8,6,4" --eval 2
```

---

## 第二步：预处理

使用 `craftsplat prepare` 命令：

1. **排序**：按文件名排序或手动指定顺序
2. **缩放**：统一缩放到长边 1600px（减少计算量，加速 COLMAP）
3. **质量检查**：自动跳过无法读取的文件
4. **Mask 生成**（可选）：使用 rembg 移除背景
5. **生成 manifest.json**：记录所有处理元数据

```bash
craftsplat prepare input_photos/ output_dir/ \
  --max-photos 20 \
  --resize 1600 \
  --mask rembg
```

**输出目录结构：**

```
output_dir/
├── images/
│   ├── 001.jpg
│   ├── 002.jpg
│   └── ...
├── masks/             (可选)
│   ├── 001_mask.png
│   └── ...
└── manifest.json
```

---

## 第三步：COLMAP 相机位姿估计

COLMAP 执行 Structure-from-Motion (SfM)：

1. **特征提取** (SIFT): 每张图检测角点和描述子
2. **特征匹配**: 在图片对之间匹配特征点
3. **稀疏重建**: 三角化得到稀疏 3D 点云和相机位姿

**关键参数：**
- `--matcher exhaustive`: 少于 50 张时使用穷举匹配，最准确
- `--matcher sequential`: 转盘序列拍摄时使用（更快但略差）
- `--quality high`: 使用较高的 SIFT 分辨率

```bash
craftsplat colmap output_dir/ --matcher exhaustive
```

**COLMAP 输出：**

```
output_dir/
├── database.db        # 特征和匹配数据库
├── sparse/
│   └── 0/
│       ├── cameras.bin
│       ├── images.bin
│       └── points3D.bin
└── ...
```

---

## 第四步：训练 3DGS 模型

使用 Nerfstudio 的 **Splatfacto** 方法（基于 gsplat）。

### Splatfacto 简介

Splatfacto 是 Nerfstudio 提供的 3DGS 实现，使用 gsplat 作为后端：
- **更快的训练速度**（相比原版 3DGS）
- **更好的内存管理**
- **内置少图增强选项**

### 训练命令

```bash
craftsplat train output_dir/ \
  --method splatfacto \
  --steps 15000
```

### 训练参数建议

| 照片数 | 推荐步数 | 理由 |
|--------|----------|------|
| 8-12 张 | 7000-10000 | 数据少，早停防止过拟合 |
| 13-18 张 | 10000-15000 | 标准配置 |
| 19-20 张 | 15000 | 完整训练 |

### 训练过程

1. **初始化**: 从 COLMAP 稀疏点云初始化 3D Gaussian
2. **前向渲染**: 使用 CUDA 光栅化渲染高斯点云
3. **Loss 计算**: L1 + SSIM 组合损失
4. **反向传播**: 更新位置、颜色、尺度、透明度、旋转
5. **自适应密度控制**: 周期性分裂/克隆/剔除高斯点
6. **重复**: 直到收敛或达到步数上限

### GPU 要求

| GPU | VRAM | 适用场景 |
|-----|------|----------|
| RTX 3060 | 12GB | ✅ 可用，20 张 × 1600px |
| RTX 4070 | 12GB | ✅ 推荐，30-60 分钟 |
| RTX 4090 | 24GB | ✅ 最佳，15-30 分钟 |
| RTX 2060 | 6GB | ⚠️ 需降分辨率至 1200px |
| 无 NVIDIA GPU | — | ❌ 无法训练 |

---

## 第五步：导出

```bash
craftsplat export output_dir/ \
  --formats ply,splat,ksplat,glb
```

### 导出格式说明

| 格式 | 用途 | 依赖 |
|------|------|------|
| `.ply` | 通用 3D 格式，MeshLab/CloudCompare 打开 | 无（Nerfstudio 内置） |
| `.splat` | SuperSplat 在线查看器格式 | 无（Nerfstudio 内置） |
| `.ksplat` | GaussianSplats3D 网页渲染格式 | 需 gsplat.js 转换 |
| `.glb` | Blender/网页可用 mesh | ⚠️ Beta，需 SuGaR/2DGS |

---

## 第六步：展示

### 方案 A：SuperSplat（推荐）

1. 导出 `.splat` 格式
2. 打开 https://playcanvas.com/supersplat
3. 拖入 `.splat` 文件
4. 获得可交互的 3D 查看器和分享链接

### 方案 B：CraftSplat-20 Web Viewer

1. 打开 `web-viewer/index.html`
2. 选择 `.ply` 或 `.splat` 文件
3. 本地预览（Beta）

### 方案 C：GaussianSplats3D

1. 安装: `npm install @mkkellogg/gaussian-splats-3d`
2. 在网页中嵌入交互式查看器

---

## 可选增强：少图优化

当 20 张照片仍不够时（如物体纹理极少、光照不佳），可使用以下 adapter：

### FSGS (Few-Shot Gaussian Splatting)

```bash
# 安装 FSGS
git clone https://github.com/VITA-Group/FSGS
cd FSGS
pip install -e .

# 使用 FSGS 训练（替代 Splatfacto）
python FSGS/train.py --config your_config
```

### SparseGS

```bash
git clone https://github.com/ForMyCat/SparseGS
# 参考其文档进行少图训练配置
```

---

## 可选增强：mesh 导出

```bash
# 使用 SuGaR 从 3DGS 提取 mesh
git clone https://github.com/Anttwo/SuGaR
cd SuGaR
python train.py --config configs/your_scene.yaml
python extract_mesh.py --checkpoint output/checkpoint.pt
```
