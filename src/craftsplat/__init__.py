"""
CraftSplat-20: 少图文创手办 3D Gaussian Splatting 建模工具链
============================================================

使用 20 张以内照片，对文创产品、手办、摆件进行高保真视觉复刻。
基于 Nerfstudio + gsplat 主线，支持可选 mesh 导出。

核心命令:
    craftsplat capture-plan   生成拍摄角度表
    craftsplat prepare        图片预处理
    craftsplat colmap         COLMAP 稀疏重建
    craftsplat train          Nerfstudio 训练
    craftsplat export         模型导出
    craftsplat report         生成运行报告
"""

__version__ = "0.1.0"
__author__ = "Laityperfect7"
