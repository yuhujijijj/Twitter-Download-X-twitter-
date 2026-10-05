# 更新日志

## 2026-10-05

- 增加可复现的 PyInstaller onedir 打包配置 `TwitterDownload.spec`。
- Windows x64 发布包包含 EXE、Python 运行时、GUI/Tk 运行组件、提示音和无凭据的初始配置。
- 放弃上传预编译 ZIP/Release 附件；用户可在 Windows 项目根目录安装 `requirements.txt` 和 PyInstaller 后运行 `python -m PyInstaller --clean --noconfirm TwitterDownload.spec`。
- 构建结果位于 `dist/app`；跨电脑使用时需复制整个 `app` 目录。
- 更新中英文 README，记录依赖安装、spec 构建和首次配置步骤。
- 发布检查：确保个人 Cookie 不进入提交或发布包。
