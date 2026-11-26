# 软件界面截图与复现

## 工作台 0.16.2

工作台、项目、连接和资源页来自 Windows 上实际运行的 0.16.2，源码为 `3ee0dde6c06f3ddd1e981ec99272379cca204a91`。白天和夜间模式分别以 3× Qt 缩放采集，使用临时数据目录，账号、节点和 Docker 工作区均未配置。

- [Windows 截图运行记录](https://github.com/engeeeee/ENGE-SPX/actions/runs/45789789216)
- [夜间 PNG 清单](../../website/public/screenshots/0.16.2/dark/capture.json) · [白天 PNG 清单](../../website/public/screenshots/0.16.2/light/capture.json)
- 截图归档 SHA-256 `1367a6c9dd9d47a676bc7dbb38ea59dbb178fc7c65d5540715cb8d0f9ba50030`

## 智能终端 0.16.2

[夜间终端](../../website/public/screenshots/0.16.2/terminal-codex@2x.png)和[白天终端](../../website/public/screenshots/0.16.2/terminal-codex-light@2x.png)来自 Linux 上实际运行的 0.16.2 智能终端与 Codex 0.169.0。两张图均为 2200×1360 原生 2× PNG，展示含两张图片和一个文件引用的未发送草稿。采集使用临时项目、本地测试服务与同一正式版应用源码。

[夜间采集清单](../../website/public/screenshots/0.16.2/terminal-capture.json) · [白天采集清单](../../website/public/screenshots/0.16.2/terminal-light-capture.json)

在 Linux 上使用官方 Codex 二进制可复现。`--theme light` 应用终端浅色预设，保存对应的图片和采集清单。

```bash
PYTHONPATH=src python docs/screenshots/capture_terminal.py \
  --codex /path/to/codex --output ./build/terminal-captures --theme light
```

## 工作台 0.15.9

工作台、项目、连接和资源页在 Windows 上以 3× Qt 缩放采集，使用 0.15.9 正式版对应的源码 `d645eee1d681c08eb097f44e020f3335dfb29fdd`。截图使用临时数据目录，账号、节点和工作区均未配置。

- [Windows 截图运行记录](https://github.com/engeeeee/ENGE-SPX/actions/runs/45323210641)
- [深色 PNG 清单及 SHA-256](../../website/public/screenshots/0.15.9/dark/capture.json) · [浅色 PNG 清单及 SHA-256](../../website/public/screenshots/0.15.9/light/capture.json)
- 原始截图归档 SHA-256 `9f9e1566fefea64865f0768eeaf9d09df969da3feda5d4814851aa092beb21f7`

## 智能终端（0.15.9）

[终端原图](../../website/public/screenshots/0.15.9/terminal-codex@2x.png)来自 ENGE SPX 0.15.9 和 Codex 0.169.0 在 Linux 上的实际运行。PNG 为 2200×1360，保留了两张图片的原生附件标记和一个文件引用。草稿保留在输入区，采集使用临时项目与本地测试服务。[版本、平台与文件校验](../../website/public/screenshots/0.15.9/terminal-capture.json)

## 工作台 0.15.6

新版工作台、项目、连接和资源页使用 Windows 上的 3× 原生采集，临时数据未配置账号或节点。文件尺寸与 SHA-256 见 [深色清单](../../website/public/screenshots/0.15.6/dark/capture.json) 和 [浅色清单](../../website/public/screenshots/0.15.6/light/capture.json)。[Windows 截图运行记录](https://github.com/engeeeee/ENGE-SPX/actions/runs/45031285658)

## 工作台 0.13.2

历史截图来自 ENGE SPX 0.13.2 在原生 Windows 环境运行的 Qt 界面，保留了工作台、项目工作区、连接与代理、资源预算页面的 PNG 原图。

| 项目 | 记录 |
| --- | --- |
| 截图时间 | 2026-11-11 16:27 UTC |
| 平台与工具 | Windows、Python 3.12.10、PySide6 6.12.0、100% Qt 缩放 |
| 运行源码 | `990d97eae580e99e3c22db454adb878dec76b90c`；应用源码与 0.13.2 正式版一致 |
| 窗口大小 | 1280 × 1000 |
| Windows 任务 | [README Windows screenshots / 43058430309](https://github.com/engeeeee/ENGE-SPX/actions/runs/43058430309) |
| 文件清单与 SHA-256 | [capture.json](../images/0.13.2/capture.json) |
| 原始 artifact SHA-256 | `cda8e2caeef5801e24155617e8731e9a3eace7a3030656f1147a33ccb7429a46` |

截图使用临时、未配置的数据目录，没有填写真实账号、节点凭据、出口或个人项目，也没有启动 Docker 工作区。尚未确认连接时，工具按钮显示为禁用，这是正常状态。它们展示界面和功能入口，不作为真实账号登录、代理连通性或用户设备长时体验的证明；功能验证另见 [0.13.2 交付报告](../validation-0.13.2.zh-CN.md)。

## 原图

- [工作台](../images/0.13.2/overview.png)：环境准备、出口信息与工作区路径。
- [项目工作区](../images/0.13.2/workspace.png)：项目目录、身份、访问权限及工具入口。
- [连接与代理](../images/0.13.2/connection.png)：落地、前置线路与本机代理配置。
- [资源预算](../images/0.13.2/resources.png)：各环境 CPU、内存上限和浏览器启动选项。

## 重新截取

在已安装项目依赖的 Windows 源码目录执行：

```powershell
$env:PYTHONPATH = 'src'
$env:QT_SCALE_FACTOR = '1'
python docs/screenshots/capture.py --output .\build\readme-screenshots
```

脚本打开真实窗口，在临时应用数据目录中切换页面、检查品牌及工具按钮未被裁切，保存 PNG 和 `capture.json`，最后关闭窗口。它不会点击启动、连接检查、登录或工具按钮，不会使用现有用户数据。

[专用 workflow](../../.github/workflows/readme-screenshots.yml)可手动运行；修改截图脚本时也会自动运行。它只生成文档截图，不构建或发布软件版本。其它平台可运行脚本预览排版，`capture.json` 会如实记录平台；更新 README 的 Windows 图时应使用 Windows 产物。

历史图片仍保留在 `docs/images/spx-*.png`，供旧版本文档引用。

## 官网高清版本（2×）

官网使用原生 Windows 2× DPI 重新截取的 2560×2000 PNG，逻辑窗口仍为 1280×1000，软件内部布局不改动。它们是软件重新渲染的截图，不是对 1× 图片进行插值或 AI 放大。

- [原生 Windows 任务 43168136679](https://github.com/engeeeee/ENGE-SPX/actions/runs/43168136679)
- [高清文件清单、逻辑尺寸、DPR 与 SHA-256](../images/0.13.2/2x/capture.json)
- [工作台](../images/0.13.2/2x/overview.png) · [项目工作区](../images/0.13.2/2x/workspace.png) · [连接与代理](../images/0.13.2/2x/connection.png) · [资源预算](../images/0.13.2/2x/resources.png)

捕获时间 2026-11-12 06:27 UTC，源码 `f607efda4fbbd839a2ed710fce48e7637d73fe20`，应用版本 0.13.2。复现时设置 `QT_SCALE_FACTOR=2`；这是当时的 2× 捕获配置；当前专用 workflow 使用下面的官网适配配置。原始 1× 文件保留供历史记录使用。

## 官网尺寸适配版本（3×）

为避免在普通 1080p 显示器上将完整宽窗口过度缩小，官网使用真实软件的响应式窗口重新截取各页面。工作台、连接和资源页面显示软件本身已有的紧凑导航；项目页保留完整导航。仅改变真实窗口尺寸和 Windows Qt DPI，没有改变字体、控件、状态或应用源码。

| 页面 | 逻辑窗口 | PNG 原始像素 |
| --- | --- | --- |
| 工作台 | 960×840 | 2880×2520 |
| 项目工作区 | 1120×1050 | 3360×3150 |
| 连接与代理 | 840×1050 | 2520×3150 |
| 资源预算 | 840×1000 | 2520×3000 |

- Windows 捕获时间：2026-11-12 07:12 UTC。
- [原生 Windows 任务 43173501032](https://github.com/engeeeee/ENGE-SPX/actions/runs/43173501032)，源码 `90a7fec5be471c24b0ff2edffb69d9972232c790`，应用仍为 0.13.2。
- [原图清单与 SHA-256](../images/0.13.2/web-3x/capture.json)。
- 原始 artifact SHA-256：`f9837bbb0b5de333971ec03f6bbf317a850baa76af68c8eec508f2edb7d23eeb`。
- [工作台](../images/0.13.2/web-3x/overview.png) · [项目工作区](../images/0.13.2/web-3x/workspace.png) · [连接与代理](../images/0.13.2/web-3x/connection.png) · [资源预算](../images/0.13.2/web-3x/resources.png)。

复现：

```powershell
$env:PYTHONPATH = 'src'
$env:QT_SCALE_FACTOR = '3'
python docs/screenshots/capture.py --profile website --output .\build\website-screenshots
```

官网首页展示区允许裁切窗口底部，点击可查看完整 PNG。普通 DPI 屏幕不对软件图片做透视变换，单个窗口仅配柔和阴影；高 DPI 屏幕保留轻微透视。1×、2× 和本批原图分别保留，README 仍引用完整导航的 2× 图。

## 智能终端（0.15.1）

[终端原图](../images/0.15.1/terminal-codex@2x.png)来自 **Linux 上实际运行的 ENGE SPX 0.15.1 `TerminalWindow` 与官方 Codex 0.169.0**。逻辑窗口 1100×680，Qt 2× 原生渲染为 2200×1360 PNG，没有生成或修改窗口内部内容；官网和中英文 README 使用同一原图。运行平台、源码提交、CLI 二进制与图片 SHA-256 见 [terminal-capture.json](../images/0.15.1/terminal-capture.json)。

截图使用临时项目与隔离 HOME。两张图片引用真实仓库文件，经现有 CLI 输入适配层传递，图片标记由 Codex 本身产生；文件路径指向实际创建的 Markdown 原件。截图保留中文草稿且不发送，没有伪造模型回复、用户账号或连通性状态。

此捕获复用现有 Linux PTY 与 CLI fixture，没有使用 Docker 或 Windows Clipboard；它展示真实产品界面，不代替 Windows + Docker 的粘贴验收，也不展示 Windows DWM/Acrylic 背景效果。相关功能验证仍见[智能粘贴验证记录](../validation-smart-clipboard.zh-CN.md)。

在已安装项目依赖的 Linux ARM64 环境，提供现有官方 Codex 二进制后可复现（脚本不会下载或安装 CLI）：

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python docs/screenshots/capture_terminal.py \
  --codex /path/to/codex --output docs/images/0.15.1 --scale 2
```

脚本使用本地 loopback fixture，没有真实账号或模型回复，不读取用户剪贴板，结束后清理临时项目。更新 Codex 版本时应实际重新捕获，不编辑图中版本或附件标记。
