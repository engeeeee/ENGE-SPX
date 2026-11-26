"use client";

import {
    createContext,
    useContext,
    useEffect,
    useRef,
    useState,
    type ReactNode,
    type CSSProperties,
} from "react";
import {
    ArrowDownToLine,
    ArrowLeft,
    ArrowRight,
    ArrowUpRight,
    Check,
    Expand,
    Menu,
    Moon,
    Sun,
    X,
    ZoomIn,
    ZoomOut,
} from "lucide-react";
import {
    asset,
    docs,
    navigation,
    product,
    screenshotPath,
    screenshots,
    themeStorageKey,
    type ScreenshotId,
    type Theme,
} from "@/lib/content";

const Site = createContext({
    openScreenshot: (_id: ScreenshotId) => {},
    theme: "dark" as Theme,
    toggleTheme: () => {},
});

export function SiteInteractions({ children }: { children: ReactNode }) {
    const [selected, setSelected] = useState<ScreenshotId>("overview");
    const [reading, setReading] = useState(false);
    const [theme, setTheme] = useState<Theme>("dark");
    const dialog = useRef<HTMLDialogElement>(null);
    const picture = screenshots.find((item) => item.id === selected)!;
    const source = screenshotPath(picture, theme);
    useEffect(() => {
        setTheme(document.documentElement.dataset.theme === "light" ? "light" : "dark");
    }, []);
    useEffect(() => {
        document.querySelector('meta[name="theme-color"]')?.setAttribute(
            "content",
            theme === "dark" ? "#000000" : "#ffffff",
        );
    }, [theme]);

    const toggleTheme = () => {
        const next = theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = next;
        setTheme(next);
        try {
            localStorage.setItem(themeStorageKey, next);
        } catch {
            // The theme remains usable in this tab when storage is unavailable.
        }
    };
    const change = (direction: number) =>
        setSelected(
            (id) =>
                screenshots[
                    (screenshots.findIndex((s) => s.id === id) +
                        direction +
                        screenshots.length) %
                        screenshots.length
                ].id,
        );

    return (
        <Site.Provider
            value={{
                theme,
                toggleTheme,
                openScreenshot(id) {
                    setSelected(id);
                    setReading(false);
                    dialog.current?.showModal();
                },
            }}
        >
            {children}
            <dialog
                ref={dialog}
                className="screenshot-dialog"
                aria-labelledby="screenshot-dialog-title"
                onClick={(event) => {
                    if (event.target === event.currentTarget)
                        dialog.current?.close();
                }}
                onKeyDown={(event) => {
                    if (reading) return;
                    if (event.key === "ArrowRight") change(1);
                    if (event.key === "ArrowLeft") change(-1);
                }}
            >
                <div className="gallery-inner">
                    <div className="gallery-toolbar">
                        <div>
                            <span className="eyebrow">
                                {picture.platform} · v{picture.version}
                            </span>
                            <h2 id="screenshot-dialog-title">
                                {picture.title}
                            </h2>
                        </div>
                        <div className="gallery-view-controls">
                            <button
                                className="gallery-reading-button"
                                aria-pressed={reading}
                                onClick={() => setReading((value) => !value)}
                            >
                                {reading ? (
                                    <ZoomOut size={15} />
                                ) : (
                                    <ZoomIn size={15} />
                                )}
                                {reading ? "适应窗口" : "放大阅读"}
                            </button>
                            <a
                                className="gallery-original"
                                href={source}
                                target="_blank"
                                rel="noreferrer"
                            >
                                高清原图 <ArrowUpRight size={13} />
                            </a>
                            <button
                                className="icon-button"
                                onClick={() => dialog.current?.close()}
                                aria-label="关闭截图"
                            >
                                <X />
                            </button>
                        </div>
                    </div>
                    <div
                        key={selected}
                        className={`gallery-image-viewport ${reading ? "is-reading" : ""}`}
                        tabIndex={0}
                        style={
                            {
                                "--shot-width": `${picture.width}px`,
                                "--shot-height": `${picture.height}px`,
                            } as CSSProperties
                        }
                        aria-label="高清软件截图，放大后可滚动阅读"
                    >
                        <img
                            src={source}
                            width={picture.width * picture.pixelRatio}
                            height={picture.height * picture.pixelRatio}
                            alt={picture.alt}
                            className="gallery-image"
                            decoding="async"
                        />
                    </div>
                    <div className="gallery-bottom">
                        <div className="gallery-select">
                            {screenshots.map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => setSelected(item.id)}
                                    aria-pressed={item.id === selected}
                                >
                                    {item.title}
                                </button>
                            ))}
                        </div>
                        <div className="gallery-arrows">
                            <button
                                className="icon-button"
                                onClick={() => change(-1)}
                                aria-label="上一张截图"
                            >
                                <ArrowLeft />
                            </button>
                            <button
                                className="icon-button"
                                onClick={() => change(1)}
                                aria-label="下一张截图"
                            >
                                <ArrowRight />
                            </button>
                        </div>
                    </div>
                    <p className="gallery-caption">
                        {picture.platform} · {picture.pixelRatio}× 截图 ·{" "}
                        {picture.width * picture.pixelRatio} ×{" "}
                        {picture.height * picture.pixelRatio} ·{" "}
                        <a
                            href={docs.screenshots}
                            target="_blank"
                            rel="noreferrer"
                        >
                            截图来源 <ArrowUpRight size={12} />
                        </a>
                    </p>
                </div>
            </dialog>
        </Site.Provider>
    );
}

export function Screenshot({
    id,
    className = "",
    priority = false,
    caption = false,
}: {
    id: ScreenshotId;
    className?: string;
    priority?: boolean;
    caption?: boolean;
}) {
    const { openScreenshot, theme } = useContext(Site);
    const item = screenshots.find((s) => s.id === id)!;
    return (
        <figure className={`product-shot ${className}`}>
            <button
                className="shot-button"
                onClick={() => openScreenshot(id)}
                aria-label={`放大查看${item.title}真实截图`}
            >
                <img
                    src={screenshotPath(item, theme)}
                    alt={item.alt}
                    width={item.width}
                    height={item.height}
                    loading={priority ? "eager" : "lazy"}
                    fetchPriority={priority ? "high" : "auto"}
                    decoding="async"
                />
                <span className="shot-zoom">
                    <Expand size={14} />
                    <span>放大截图</span>
                </span>
            </button>
            {caption && (
                <figcaption>
                    {item.platform} · v
                    {item.version}{" "}
                    ·{" "}
                    {item.context}
                </figcaption>
            )}
        </figure>
    );
}

export function Navigation() {
    const dialog = useRef<HTMLDialogElement>(null);
    const [active, setActive] = useState("");
    const { theme, toggleTheme } = useContext(Site);
    const themeLabel = theme === "dark" ? "切换到浅色模式" : "切换到深色模式";
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    const id = entry.target.id;
                    if (entry.isIntersecting) setActive(id);
                    else setActive((current) => (current === id ? "" : current));
                }
            },
            { rootMargin: "-15% 0px -60% 0px" },
        );
        navigation.forEach(({ id }) => {
            const element = document.getElementById(id);
            if (element) observer.observe(element);
        });
        return () => observer.disconnect();
    }, []);
    return (
        <>
            <a className="skip-link" href="#main">
                跳到主要内容
            </a>
            <header className="site-header">
                <div className="nav-inner">
                    <a href="#" className="brand" aria-label="ENGE SPX 首页">
                        <img
                            src={asset("/brand/logo.svg")}
                            alt=""
                            width="35"
                            height="35"
                        />
                        <span>ENGE SPX</span>
                    </a>
                    <nav className="desktop-nav" aria-label="主要导航">
                        {navigation.map(({ id, label }) => (
                            <a
                                key={id}
                                href={`#${id}`}
                                aria-current={
                                    active === id ? "location" : undefined
                                }
                            >
                                {label}
                            </a>
                        ))}
                        <a
                            href={docs.quickstart}
                            target="_blank"
                            rel="noreferrer"
                        >
                            文档
                        </a>
                    </nav>
                    <div className="nav-actions">
                        <a
                            className="nav-github"
                            href={product.repository}
                            target="_blank"
                            rel="noreferrer"
                        >
                            GitHub
                        </a>
                        <a
                            className="button button-small button-primary nav-download"
                            href={product.installer}
                        >
                            <ArrowDownToLine size={15} />
                            下载 Windows 版
                        </a>
                        <button className="theme-button icon-button" aria-label={themeLabel} title={themeLabel} onClick={toggleTheme}>
                            {theme === "dark" ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
                        </button>
                        <button
                            className="menu-button icon-button"
                            aria-label="打开导航菜单"
                            aria-haspopup="dialog"
                            onClick={() => dialog.current?.showModal()}
                        >
                            <Menu />
                        </button>
                    </div>
                </div>
            </header>
            <dialog ref={dialog} className="mobile-menu" aria-label="导航菜单">
                <div className="mobile-menu-head">
                    <a
                        href="#"
                        className="brand"
                        onClick={() => dialog.current?.close()}
                    >
                        <img
                            src={asset("/brand/logo.svg")}
                            alt=""
                            width="35"
                            height="35"
                        />
                        <span>ENGE SPX</span>
                    </a>
                    <button
                        className="icon-button"
                        onClick={() => dialog.current?.close()}
                        aria-label="关闭导航菜单"
                    >
                        <X />
                    </button>
                </div>
                <nav>
                    {navigation.map(({ id, label }) => (
                        <a
                            key={id}
                            href={`#${id}`}
                            onClick={() => dialog.current?.close()}
                        >
                            {label}
                        </a>
                    ))}
                    <a
                        href={docs.quickstart}
                        target="_blank"
                        rel="noreferrer"
                        onClick={() => dialog.current?.close()}
                    >
                        使用文档
                    </a>
                </nav>
                <a className="button button-primary" href={product.installer}>
                    <ArrowDownToLine size={17} />
                    下载 Windows 安装版
                </a>
                <p>v{product.version} · Windows x64</p>
            </dialog>
        </>
    );
}

export function CopyChecksum() {
    const [copied, setCopied] = useState(false);
    const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
    useEffect(
        () => () => {
            if (timer.current) clearTimeout(timer.current);
        },
        [],
    );
    return (
        <button
            className="text-button checksum-button"
            onClick={async () => {
                try {
                    await navigator.clipboard.writeText(
                        product.installerSha256,
                    );
                    setCopied(true);
                    if (timer.current) clearTimeout(timer.current);
                    timer.current = setTimeout(() => setCopied(false), 2500);
                } catch {
                    window.open(
                        product.release,
                        "_blank",
                        "noopener,noreferrer",
                    );
                }
            }}
        >
            <Check size={13} />
            <span aria-live="polite">
                {copied ? "安装版 SHA-256 已复制" : "复制安装版 SHA-256"}
            </span>
        </button>
    );
}
