import { Screenshot } from "@/components/interactions";
import { docs } from "@/lib/content";

export function ResourcesSection() {
    return (
        <section id="resources" className="section resource-section" aria-labelledby="resources-title">
            <div className="container showcase showcase-reversed">
                <div className="showcase-copy">
                    <h2 id="resources-title">资源与性能</h2>
                    <p>选择标准或低资源模式，查看容器占用，也可以单独关闭浏览器。</p>
                    <a className="text-link" href={docs.resources}>预算设置与资源监控</a>
                </div>
                <div className="showcase-image">
                    <Screenshot id="resources" className="shot-cropped" caption />
                </div>
            </div>
        </section>
    );
}
