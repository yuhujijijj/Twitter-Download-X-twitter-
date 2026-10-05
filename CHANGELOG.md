# 更新日志

## 2026-10-05

- 增加可复现的 PyInstaller onedir 打包配置 `TwitterDownload.spec`。
- Windows x64 发布包包含 EXE、Python 运行时、GUI/Tk 运行组件、提示音和无凭据的初始配置。
- 发布包以 ZIP 形式作为 GitHub Release 附件分发；源码仓库不跟踪本机 `app/` 构建目录。
- 更新中英文 README，说明 Release 下载、解压和首次配置步骤。
- 发布检查：确保个人 Cookie 不进入提交或发布包。
