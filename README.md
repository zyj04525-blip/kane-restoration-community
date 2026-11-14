# 凯恩战记（Kai En Zhan Ji）｜非官方社区还原项目

这是一个面向老网页游戏《凯恩战记》玩家的开源还原项目。目前发布的是**本地战斗原型和还原研究资料**，不是原版客户端，也不是完整重制版。不需要原版素材或游戏账号，就能体验「海之轻语」的基础走位、三段普攻和六个技能的逻辑预览。

## 为什么开源？

手头的角色美术、完整动作和独立技能音效不够，暂时没法继续完成。与其让已有的代码和研究记录搁置，不如开放出来，让感兴趣的玩家和开发者接着做。

- **想参与还原？** 可以从前端战斗、角色动作、特效或原创音效入手，先看[当前缺口](docs/STATUS.md)和[贡献指南](CONTRIBUTING.md)。
- **手上有旧录像或资源线索？** 可以[提交 Issue](https://github.com/zyj04525-blip/kane-restoration-community/issues/new/choose)，先说明来源和授权，不要直接上传权利不明的文件。
- **只想看看做到了哪里？** 按下方「先运行」即可打开本地预览。预览用几何图形代表角色和技能范围，不是原版画面。

**项目与原运营方无关。** 仓库不附原版游戏源码、美术或音频；MIT 只覆盖本项目有权许可的代码和文档。

## 现在有什么

- 可运行的本地战斗逻辑：走位、双击冲刺、三段普攻、海之轻语六技能、敌人行为、暂停与胜负结算。
- 已有创建角色、漫画过场、入场与战斗界面代码；接入本地图片后才能显示这些画面。
- 593条战斗图层记录、入场取帧记录及14个图像分析/对照脚本，保留定位、时间和遮挡限制。
- 308条官方录像播放线索。2026-11-12查到播放信息并验证原始地址响应头，未逐条播放验证，不是308份独立游戏素材。
- 无需游戏素材即可运行的逻辑预览，供贡献者检查代码。几何图形只显示角色位置与作用范围，不代表原版美术。

## 先运行

安装 Python 3.10+，在本目录运行：

```sh
python tools/serve.py
```

打开 <http://127.0.0.1:8765/demo/>。服务器只监听本机，不连接原游戏服务器，不需要游戏账号。

WASD/方向键移动，双击 A/D 冲刺，J 普攻，H/U/N/I/O/L 技能，Esc 暂停，R 重置。也可使用页面按钮。当前没有玩家跳跃系统；敌人可被技能击飞。

安装 Node.js 18+ 后可运行现有战斗测试，无需 npm 安装：

```sh
node playable/engine.test.cjs
python -m unittest discover -s tests -p "test_*.py"
python tools/audit_release.py
```

## 如果你有原版资源

优先需要 **原版 SWF / 图片图集、人物动作完整周期、独立技能音效、原版配置与登录选服画面**。

1. 先保留原文件，不运行来源不明的 EXE。
2. 提供来源、保存日期、原文件名/目录、文件大小与 SHA-256；不确定是不是原版也请写清楚。
3. 通过资源线索 Issue 提供公开来源。不要上传账号、Cookie、完整浏览器配置或含私人数据的整个缓存目录。
4. 已确认可以公开分发的文件才进入仓库；来源或许可不明确时先提交说明及指纹。

接入格式与本地导入步骤见 [素材接入](docs/ASSETS.md)。贡献方式见 [CONTRIBUTING](CONTRIBUTING.md)，缺口见 [当前状态](docs/STATUS.md)。

## 不要把这些误认为原版

伤害、耗蓝、冷却、碰撞范围、移动速度和敌人行为多数是重建估计。测试通过只证明代码自洽，不证明还原准确。

现有帧记录来自录像观察；透明边缘、遮挡区、完整时序仍不确定。录像背景音乐不能替代技能音效，音效目前留空。不能因为项目出现了六个技能，就称它们已完整还原。

## 目录

| 位置 | 内容 |
| --- | --- |
| `playable/` | 战斗状态机、渲染适配器与原有测试 |
| `entry/` | 现有入场流程代码，不附第三方图片 |
| `demo/` | 不依赖游戏图片的逻辑预览 |
| `reference/` | 取帧记录、素材接口示例、录像线索与代码来源说明 |
| `tools/reconstruction/` | 历史图像处理实验，输入由贡献者自行提供 |
| `tools/` | 本地预览、素材导入、发布检查和源码打包 |
| `docs/` | 状态、来源、接入和 GitHub 发布说明 |

## 许可与发布范围

本项目自行编写的代码采用 [MIT License](LICENSE)，允许他人使用、修改与再分发；它不把原游戏或其他玩家素材变成开源素材。第三方图片、视频、音频、字体、游戏标识与提取代码不包含在该许可中，见 [NOTICE](NOTICE.md)。

这个源码包不附原游戏媒体、不附未知程序、不附玩家评论原文或个人资料。**没有恢复原版美术不等于项目已经完成**，所有替换都应保留可追溯的证据。

## English

An unofficial, unfinished preservation/reconstruction project for the Chinese browser game 凯恩战记 (Kai En Zhan Ji). It includes our reconstruction code, timing/anchor research, and public footage references. It does **not** contain the original game source, a complete client, or redistributable original media. The asset-free demo is a logic harness, not a visual recreation. Contributions of documented, safely handled original resources are welcome. MIT covers our code only; third-party rights are separate.
