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
        title: "SSH 智能终端 · 多会话侧栏与自动重连",
        summary:
            "容器与 SSH 会话共用可收起左侧会话栏，也可一键拆为「独立窗口」并保持连接不断。支持 10,000 行历史回看、Tab 行内补全与断线自动重连（1–30 秒退避）；按下 Ctrl+V 自动走 SFTP 上传截图或文件并填入远端路径。",
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
        title: "指纹核验与断线自动重连",
        detail: "握手均核验主机公钥指纹；网络断开后保留 10,000 行历史并按 1–30 秒退避自动重连。",
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
