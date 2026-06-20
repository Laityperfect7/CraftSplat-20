# Changelog

All notable changes to CraftSplat-20 will be documented in this file.

## [0.1.0] — 2025-06-20

### Added
- Initial release: CraftSplat-20 core CLI toolchain
- `craftsplat capture-plan` — 生成 20 张以内拍摄角度表
- `craftsplat prepare` — 图片预处理、排序、压缩、mask 生成
- `craftsplat colmap` — COLMAP wrapper（外部命令）
- `craftsplat train` — Nerfstudio Splatfacto wrapper（外部命令）
- `craftsplat export` — 导出 ply/splat/ksplat/glb
- `craftsplat report` — 生成运行报告
- 完整中文文档：拍摄指南、可行性分析、技术流程、故障排除
- Web Viewer 占位页面（本地 .ply/.splat 加载 UI）
- GitHub Actions CI：ruff 检查 + pytest
- MIT License
