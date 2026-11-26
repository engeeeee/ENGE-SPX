# ENGE SPX 官方网站

正式网站：**https://enge1337.cn/**

Next.js 静态导出、React、TypeScript、Lucide 与 CSS 设计变量。官网介绍实际的 Windows AI 编程工作台，生产环境由 Nginx 直接提供 HTML/CSS/JS，不需要新增 Node 常驻服务。

## 本地运行与构建

需要 Node.js 20.9+：

```bash
cd website
npm ci
npm run dev
```

打开 `http://127.0.0.1:4173`。生成静态站：

```bash
npm run build
```

产物为 `out/`。构建包含 TypeScript 检查；`npm run typecheck` 可单独执行。依赖版本由 `package-lock.json` 固定。

## 源码与内容位置

```text
src/app/page.tsx                  页面组合与结构化 SEO 数据
src/app/layout.tsx                站点元数据、字体和全局交互
src/app/globals.css               颜色、排版、布局、响应式和动效
src/components/sections/          工作区、终端、SSH/SFTP、网络等分区与 Footer
src/components/architecture.tsx   两种接入模式与网络路径示意
src/components/interactions.tsx   导航、高清截图浏览器、校验值复制
src/lib/content.ts               版本、真实下载地址、文档、截图、FAQ
public/brand/logo.svg             仓库原始 Logo
public/screenshots/               原始软件截图与来源清单
scripts/capture-previews.mjs      短浏览器检查和实际网页预览
scripts/deploy-static.py          Linux 上的静态目录原子发布
```

更新软件版本时，修改 `src/lib/content.ts` 中的版本、发布日期、Releases 与附件地址、SHA-256。下载地址应先从真实 [GitHub Releases](https://github.com/engeeeee/ENGE-SPX/releases)核对。截图版本单独标识，不用新版本号描述旧界面。

## 软件截图的真实性与清晰度

官网默认夜间模式，右上角可切换并记住选择。工作台、连接、项目和资源页使用 **0.16.2 Windows** 两种主题的原生 3× 截图，点开原图后可按原始逻辑尺寸阅读。采集记录和 SHA-256 位于 `public/screenshots/0.16.2` 中各主题的 `capture.json`。

终端截图使用 **0.16.2 Linux 产品终端与 Codex 0.169.0**（2200×1360 原生 2× 图，展示未发送的测试草稿）；分组与 SSH 智能终端使用 **0.16.5 真实 Qt 多会话界面**、远程 SSH 页面与 SFTP 管理器使用 0.16.2 界面及 RFC 5737 示例服务器地址以 2× 渲染展示。[图片来源与展示方式](DESIGN.md)

## 预览与简短检查

按维护者要求，仅做构建、主要链接/交互及桌面/手机排版检查，没有运行长时间回归。

开发服务器运行时，可生成真实网页截图：

```bash
npx playwright install chromium
npm run preview:capture
```

也可设置 `PREVIEW_URL=https://enge1337.cn` 截取正式网站。已有 Chromium 时可用 `CHROMIUM_PATH` 指定可执行文件；`CAPTURE_ONLY=1` 只更新预览，不重复交互检查。预览写入 `previews/`，包括六个主要分区、桌面长图、1920px、平板、移动端。捕获时启用减少动态效果以固定画面，线上尊重访问者的 `prefers-reduced-motion`。

线上交付入口：[网页预览](https://enge1337.cn/previews/)、[完整源码 ZIP](https://enge1337.cn/deliverables/ENGE-SPX-website-source.zip)、[全部预览 ZIP](https://enge1337.cn/deliverables/ENGE-SPX-website-previews.zip)。

## 部署

### 当前服务器 / Nginx

域名、TLS、Cloudflare 沿用已有设置。将已有 HTTPS 虚拟主机的站点内容指向 `/srv/enge-spx/current`；示例见 [deploy/nginx-static.conf.example](deploy/nginx-static.conf.example)。首次切换前备份旧配置与数据，执行 `nginx -t` 后再 reload。

后续发布：

```bash
npm ci
npm run build
python3 scripts/deploy-static.py --root /srv/enge-spx
```

脚本创建新 release、保留上次构建的哈希静态资源并原子切换 `current`，不会删除旧目录或修改 Nginx。回滚时将 `current` 原子指回上个 release。旧站点的系统配置备份由服务器运维单独保存，不进入源码归档。

### 其它静态平台

| 平台 | 设置 |
| --- | --- |
| Cloudflare Pages | 根目录 `website`，构建 `npm run build`，输出 `out` |
| Vercel | 根目录 `website`；按 Next.js 静态导出构建 |
| GitHub Pages | 构建 `out` 并发布；项目路径可在构建前设置 `NEXT_PUBLIC_BASE_PATH=/ENGE-SPX` |
| 任意静态服务器 | 提供 `out/`，未知路由返回 `404.html`，不要改写成首页 |

已有官网的 canonical 为 `https://enge1337.cn/`。迁移域名时更新 `src/lib/content.ts` 的 `site` 与相应 SEO 配置。`public/.nojekyll` 用于保留 GitHub Pages 的 `_next` 目录。

## 许可

网站源码沿用项目的 **PolyForm Noncommercial 1.0.0**，见 [LICENSE](LICENSE)。第三方依赖与 Geist 字体声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)，相应许可证文本位于 `public/licenses/`。
