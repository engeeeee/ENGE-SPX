# ENGE SPX 官网设计

暖白画布、宋体与西文衬线标题、陶土色主按钮。配色和排版变量集中在 `src/app/globals.css`。终端区沿用软件的暖深灰，其他分区通过分隔线、留白和图文位置区分。[Anthropic](https://www.anthropic.com/) · [Claude 设计参考](https://github.com/VoltAgent/awesome-design-md/tree/fcc70284932276d085f01ef9f83edde90b1258cb)

首页先介绍产品用途和下载方式，随后展示工作区、两种代理路径、终端与资源控制。安装步骤、常见问题和文档入口集中在页尾。通过 `src/lib/content.ts` 更新产品版本、下载及截图来源。

截图来自项目仓库。首屏从顶部展示一张清晰的 Windows 工作台，点击可查看全图或按原始逻辑尺寸阅读。工作台与设置截图来自 Windows v0.13.2，终端截图来自 Linux 上实际运行的 v0.15.1 与 Codex。软件图内的界面保持原样，网络路径图为单独的架构示意。

代理图标明第一跳与落地出口。SOCKS5、HTTP、HTTPS 是落地协议的可选项。本机 v2ray 模式的按目标分流由外部客户端控制。
