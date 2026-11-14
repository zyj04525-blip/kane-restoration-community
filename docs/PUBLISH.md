# 准备发布到GitHub

建议仓库名：`kane-restoration-community`。

建议描述：凯恩战记非官方社区还原研究：本地战斗原型、录像对照记录与资源协作。未达1:1，不含原版客户端/第三方素材。

先运行README中的测试和`python tools/audit_release.py`，检查LICENSE/NOTICE与`git diff --cached`。新仓库请选择Public；上传**本源码包内的文件**，不要上传上级旧工作目录、整个研究缓存或原有单文件试玩HTML（可能内嵌第三方媒体）。

本地发布步骤（仓库地址换成你自己创建的空仓库）：

```sh
git init
git add .
git diff --cached --stat
git commit -m "Prepare community restoration research starter"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/kane-restoration-community.git
git push -u origin main
```

也可在GitHub网页中上传本目录内容，包括`.github`与`.gitignore`。首次发布不要开启自动公开游戏素材的站点部署。

Issue模板已包含资源线索和还原偏差；PR模板要求来源与验证说明。后续发布源码ZIP：

```sh
python tools/package_release.py
```

打包只采用`RELEASE_FILES.json`明确列出的文本文件；本地导入的图片、缓存与视频不会被自动带入。增加可公开的源文件后须更新此清单。`SHA256SUMS.txt`是包内文件指纹，压缩包旁的`.sha256`用于核对包本身，二者都不是无毒保证。

本准备包没有自动创建仓库、推送代码、发布Release或给玩家发送消息。
