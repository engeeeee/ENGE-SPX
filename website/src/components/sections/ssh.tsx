"use client";

import { useState } from "react";
import {
    ArrowUpRight,
    FileUp,
    FolderSync,
    KeyRound,
    Server,
    ShieldCheck,
    Terminal,
} from "lucide-react";
import { Screenshot } from "@/components/interactions";
import { docs, type ScreenshotId } from "@/lib/content";

const sshViews = [
    {
        id: "ssh" as ScreenshotId,
        icon: Server,
        title: "SSH 主机管理与本地凭据加密",
        summary:
            "集中保存常用服务器，支持密码或私钥文件登录，也支持不落盘的「临时连接」与多因素认证交互；密码与私钥口令可选通过 Windows 当前用户 DPAPI 加密存储在本地。",
    },
    {
        id: "ssh-terminal" as ScreenshotId,
        icon: Terminal,
        title: "SSH 智能终端 · Ctrl+V 自动上传截图",
        summary:
            "双击服务器即在独立任务栏窗口中打开 SSH 会话。支持微软 ConPTY 万行（10,000 行）滚动回看与 Tab 行内补全；按下 Ctrl+V 或右键粘贴本机截图/文件时，自动通过 SFTP 上传并把远端路径填入命令行。",
    },
    {
        id: "sftp" as ScreenshotId,
        icon: FolderSync,
        title: "内置 SFTP 文件管理器",
        summary:
            "可从「远程 SSH」页面或已开启的 SSH 终端顶部工具栏直接进入 SFTP。支持远端目录路径导航、多选文件上传、下载、新建文件夹与传输进度控制，使用系统 OpenSSH SFTP v3。",
    },
] as const;

const sshGuarantees = [
    {
        icon: KeyRound,
        title: "Windows DPAPI 保护",
        detail: "密码/私钥口令仅用当前 Windows 账户 DPAPI 加密保存，不上传云端；编辑时可随时清除凭据。",
    },
    {
        icon: ShieldCheck,
        title: "首次主机指纹核对",
        detail: "直连终端与 SFTP 首次握手均弹出服务器公钥指纹供你核验，已知主机记录一致校验后继续。",
    },
    {
        icon: FileUp,
        title: "Ctrl+V 直传远端目录",
        detail: "截图或文件自动传至远端 ~/.enge-spx-paste-* 目录，单文件上限 128 MiB、单批上限 256 MiB。",
    },
    {
        icon: FolderSync,
        title: "原子临时文件防覆盖",
        detail: "上传先写入 .enge-spx-upload-*.part，完成后移动到位；下载完毕才生成最终本地文件。",
    },
] as const;

export function SshSection() {
    const [active, setActive] = useState<ScreenshotId>("ssh");
    return (
        <section
            id="ssh"
            className="section section-band"
            aria-labelledby="ssh-title"
        >
            <div className="container">
                <div className="section-intro">
                    <div>
                        <span className="kicker">REMOTE SSH & SFTP</span>
                        <h2 id="ssh-title">原生远程 SSH 终端与内置 SFTP</h2>
                    </div>
                    <div className="section-intro-copy">
                        <p>
                            无需为连接线上服务器再切换第三方终端或 FTP 客户端。ENGE SPX 使用本机网络和系统 OpenSSH 客户端直连远程服务器，将常用主机管理、截图粘贴直传与 SFTP 文件管理集成在同一套桌面体验中。
                        </p>
                        <div className="text-links">
                            <a className="text-link" href={docs.ssh}>
                                SSH 连接与粘贴上传{" "}
                                <ArrowUpRight size={13} aria-hidden="true" />
                            </a>
                            <a className="text-link" href={docs.sftp}>
                                SFTP 文件管理说明{" "}
                                <ArrowUpRight size={13} aria-hidden="true" />
                            </a>
                        </div>
                    </div>
                </div>
                <div className="ssh-layout">
                    <div
                        className="ssh-tabs"
                        role="tablist"
                        aria-label="远程 SSH 功能模块"
                    >
                        {sshViews.map(({ id, icon: Icon, title, summary }) => (
                            <button
                                key={id}
                                role="tab"
                                className="ssh-tab"
                                aria-selected={active === id}
                                onClick={() => setActive(id)}
                            >
                                <span className="ssh-tab-head">
                                    <Icon size={17} aria-hidden="true" />
                                    <span>{title}</span>
                                </span>
                                <p>{summary}</p>
                            </button>
                        ))}
                    </div>
                    <div className="ssh-stage" role="tabpanel">
                        <Screenshot id={active} caption />
                    </div>
                </div>
                <div className="ssh-specs">
                    {sshGuarantees.map(({ icon: Icon, title, detail }) => (
                        <div className="ssh-spec" key={title}>
                            <strong>
                                <Icon size={15} aria-hidden="true" />
                                <span>{title}</span>
                            </strong>
                            <p>{detail}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
