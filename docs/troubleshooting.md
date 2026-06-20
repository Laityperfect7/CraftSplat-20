# 故障排除指南

> 常见问题和解决方案，覆盖从拍摄到训练的完整流程。

---

## COLMAP 相关

### 问题：COLMAP 特征提取后匹配点极少（<100 对匹配）

**可能原因：**
1. 照片间光照差异太大（自动曝光导致）
2. 物体缺乏纹理（纯色表面）
3. 照片分辨率太低
4. 物体表面有强烈镜面反射

**解决方案：**
- 使用手动曝光，固定所有相机参数
- 在物体表面添加临时纹理（如用投影仪投射图案），或使用哑光涂层
- 确保照片分辨率 ≥2000px 长边
- 使用偏光镜消除反光
- 提高 SIFT 特征检测灵敏度：
  ```bash
  colmap feature_extractor --SiftExtraction.max_num_features 8192
  ```

### 问题：COLMAP mapper 失败，报 "no good initial image pair found"

**可能原因：**
- 照片之间重叠不够（角度间隔太大）
- 照片顺序混乱（未按角度排列）
- 物体在照片间发生了移动

**解决方案：**
- 减小角度间隔：每环增加到 10-12 张
- 确保相邻照片有 ≥60% 的重叠区域
- 使用转盘拍摄，确保物体姿态不变
- 如果使用 sequential matcher，确保照片是按拍摄顺序排列的

### 问题：稀疏重建成功但相机位姿不完整（部分照片位姿缺失）

**可能原因：**
- 部分照片模糊或对焦不准
- 部分照片背景混乱导致特征匹配偏移

**解决方案：**
- 删除模糊的照片，用相邻角度照片替代
- 对照片生成 mask 以排除背景干扰：
  ```bash
  craftsplat prepare INPUT OUTPUT --mask rembg
  craftsplat colmap OUTPUT --use-masks
  ```
- 使用 `--matcher exhaustive` 提高匹配率

---

## 训练相关

### 问题：训练刚开始就 OOM（显存不足）

**可能原因：**
- 照片分辨率过高
- GPU 显存不足（<8GB）
- 背景区域太大，生成了过多高斯点

**解决方案：**
- 降低照片分辨率：
  ```bash
  craftsplat prepare INPUT OUTPUT --resize 1200
  ```
- 使用 mask 移除背景，减少无关高斯点
- 减少最大高斯点数：
  ```bash
  # 在 train 命令中添加参数
  craftsplat train OUTPUT --method splatfacto --steps 10000
  # 然后在 Nerfstudio 配置中设置较低的上限
  ```
- 换用更大显存的 GPU

### 问题：训练 loss 不下降/下降极慢

**可能原因：**
- COLMAP 位姿估计质量差
- 学习率设置不当
- 初始化高斯点过少或位置不佳

**解决方案：**
- 检查 COLMAP 重建质量（至少 1000+ 稀疏点）
- 使用 Splatfacto 的默认学习率（通常已优化好）
- 确保 COLMAP 位姿注册了所有训练照片
- 从更简单的物体开始测试（如哑光、多纹理的手办）

### 问题：重建结果模糊/过度平滑

**可能原因：**
- 训练步数不足
- 照片本身模糊（运动模糊、对焦不准）
- 照片分辨率降低太多

**解决方案：**
- 增加训练步数至 20000-30000
- 使用三脚架拍摄，确保每张照片清晰
- 不要过度降低分辨率（保持在 1600px 以上）
- 检查每张照片的清晰度，删除模糊的：
  ```python
  import cv2
  for img in images:
      score = cv2.Laplacian(img, cv2.CV_64F).var()
      if score < 50:  # 模糊阈值
          print(f"模糊: {img}")
  ```

---

## 导出与展示

### 问题：.ply 文件在 MeshLab 中打开是空的

**可能原因：**
- PLY 文件格式不是标准格式
- 导出过程中断

**解决方案：**
- 使用 CloudCompare 替代 MeshLab 打开
- 检查 PLY 文件头格式
- 重新导出

### 问题：SuperSplat 加载 .splat 文件后黑屏

**可能原因：**
- .splat 文件不兼容 SuperSplat 版本
- 浏览器不支持 WebGPU

**解决方案：**
- 使用最新版 Chrome/Edge（WebGPU 支持）
- 确保 .splat 是 Nerfstudio 最新版导出的
- 或者使用 GaussianSplats3D 加载 .ply 文件

### 问题：Web Viewer 无法加载文件

**Web Viewer 目前是占位实现**，不包含完整的 WebGL 渲染器。
- 使用 SuperSplat (https://playcanvas.com/supersplat) 进行在线展示
- 或集成 GaussianSplats3D 到 Web Viewer 中

---

## 拍摄相关

### 问题：物体顶部或底部缺失

**原因**: 仰角范围不够大，没有覆盖顶部和底部视角。
**解决**:
- 上环仰角提高到 +50°
- 增加下环到 -35°
- 或增加纯顶视图和纯底视图各 1 张

### 问题：转盘式拍摄导致 COLMAP 误判相机运动

**原因**: COLMAP 默认假设场景静态、相机运动。如果物体不动、转盘旋转，相机相对于物体是静止的，但 COLMAP 无法区分。

**解决方案**:
- 保持转盘不动，手动环绕物体拍摄
- 或使用固定相机 + 旋转转盘 + COLMAP 专用模式
- 或使用 AprilTag 标记在转盘上以帮助 COLMAP 区分运动

---

## 获取帮助

如果上述方案无法解决你的问题：

1. **查看上游文档**:
   - [COLMAP FAQ](https://colmap.github.io/faq.html)
   - [Nerfstudio Docs](https://docs.nerf.studio/)
   - [gsplat GitHub Issues](https://github.com/nerfstudio-project/gsplat)

2. **提交 Issue**:
   - GitHub: https://github.com/Laityperfect7/CraftSplat-20/issues
   - 请附上: 照片数量、分辨率、COLMAP 日志、GPU 型号、完整错误信息
