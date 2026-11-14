# 素材接入

公开包不含游戏图片。`demo/`不需要素材；`entry/`需要完整的本地资源结构。

## 接现有渲染器

准备一个本地文件夹，结构如下。只使用你有权处理的文件；能本地使用不等于已经获得公开分发许可。

```text
your-asset-pack/
  entry/assets/manifest.json
  entry/assets/male0.webp
  entry/assets/…
  playable/assets-v6/manifest.json
  playable/assets-v6/arena.webp
  playable/assets-v6/idle-0.webp
  playable/assets-v6/…
```

可参考 `reference/entry-manifest.json` 和 `reference/combat-manifest.json` 的结构，但不能把里面的来源/指纹直接套在新文件上。

```sh
python tools/import_assets.py --source /path/to/your-asset-pack --check-only
python tools/import_assets.py --source /path/to/your-asset-pack
python tools/serve.py
```

然后打开 <http://127.0.0.1:8765/entry/>。导入只读取JSON和清单引用的WebP/可选外框图，不解压、不下载、不执行程序。先校验全部输入，再复制；目标已有不同文件时拒绝覆盖，可加 `--replace` 明确替换。素材目录默认不进Git。

导入检查文件路径、清单基本结构与媒体文件头，不能证明文件无恶意内容，也不能验证来源、版权或1:1准确度。该工具不自动把SWF转换为当前格式。

## 战斗图层约定

- 舞台是960×560；角色`x/y`是场景中的脚底锚点，帧中的`anchor`是图片局部像素坐标。渲染时按朝向镜像，不能逐帧随意重新居中。
- `layers`记录`name`（不含扩展名）、`kind`、`at_ms`、`anchor:[x,y]`、`dimensions:[w,h]`；各`kind`按`at_ms`递增排列。实际图片是`name.webp`。
- `animations[kind]`包含`duration_ms`和可选的`loop`（省略表示不循环）。静态`guard`可省略`at_ms`。时间来自可靠证据；录像25fps不等于客户端一定25fps。
- 基础组：`idle`、`walk`、`guard`、`attack0/1/2`、`water0/1/2`；技能组：`cast-h/u/n/i/o/l`、`skillfx-h/u/n/i/o/l`。图标组`icon-*`可选。
- 背景是`arena.webp`。与原界面整合的HUD目前有硬编码位置，换素材规格时要一起审查`playable/arena.js`。
- 原版音效待找回，当前代码未接音频。不要以整段录像音轨或其他游戏的声音填充。

入场清单的`frames`映射为独立960×560图片；`animations`以一张5列×2行图集最多10帧组织，时序由现有代码按40ms步进，是原型约束。未来拿到原始帧表应修改播放器而非强行压成此格式。

## 历史录像分析脚本

`tools/reconstruction/`保留14个原有图像分析与核对脚本，仅供研究。它们不是通用原版素材恢复器，也不能恢复被遮住的原始像素。本次做了路径可移植化与语法检查，**没有在干净环境重新跑完全部图像流水线**。

可选依赖为`av`、`numpy`、`Pillow`（见该目录的`requirements.txt`）。使用环境变量`KANE_RESEARCH_INPUT_DIR`指定输入目录；`KANE_RESEARCH_WORK_DIR`指定输出工作区，默认本项目的`private-work/`。`KANE_QA_FONT`可指向本地中文字体；未提供时校对图文字可能缺字。

输入包括`official-footage-229512.f4v`，另把狼王片段放到工作区`research/skills/ocean-wolf-228847.f4v`。入口图提取用`prepare_entry_assets.py`。战斗历史顺序为：`extract_playable_assets`→`refine_playable_assets`→`extract_ocean_skills`→`refine_ocean_casts`→`restore_ocean_highlights`→`repair_ocean_quality`→`trim_detached_body_pixels`→`refine_locomotion_edges`→`recover_walk_cycle`→`recover_water_curtain`。这条顺序仅说明依赖关系，不承诺对任意录像有效。

生成物保留在私人工作区，审查后按上面的导入步骤使用。官方网站外框图片不由这些脚本完整生成，需要另有可用来源；外框为可选资源，离线打包工具则仍要求对应外框文件齐备。
