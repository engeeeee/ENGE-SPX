import { Navigation } from "@/components/interactions";
import { docs, product } from "@/lib/content";
import { HeroSection } from "@/components/sections/hero";
import { FeaturesSection } from "@/components/sections/features";
import { WorkspaceSection } from "@/components/sections/workspace";
import { NetworkSection } from "@/components/sections/network";
import { TerminalSection } from "@/components/sections/terminal";
import { SshSection } from "@/components/sections/ssh";
import { ResourcesSection } from "@/components/sections/resources";
import { GetStartedSection } from "@/components/sections/get-started";
import { FaqSection } from "@/components/sections/faq";
import { Footer } from "@/components/sections/footer";

export default function Home() {
    const structuredData = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        name: product.name,
        applicationCategory: "DeveloperApplication",
        operatingSystem: "Windows x64",
        softwareVersion: product.version,
        url: product.site,
        downloadUrl: product.installer,
        license: docs.license,
        description:
            "Windows AI 编程隔离工作台，集成 Docker 容器工作区、双跳代理出口核验、智能粘贴终端、远程 SSH 会话与 SFTP 文件管理。",
    };
    return (
        <>
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{
                    __html: JSON.stringify(structuredData).replace(
                        /</g,
                        "\\u003c",
                    ),
                }}
            />
            <Navigation />
            <main id="main">
                <HeroSection />
                <FeaturesSection />
                <WorkspaceSection />
                <NetworkSection />
                <TerminalSection />
                <SshSection />
                <ResourcesSection />
                <GetStartedSection />
                <FaqSection />
            </main>
            <Footer />
        </>
    );
}
