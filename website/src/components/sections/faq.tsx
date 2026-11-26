import { ArrowUpRight } from "lucide-react";
import { docs, faqs } from "@/lib/content";

export function FaqSection() {
    return (
        <section
            id="faq"
            className="section container faq-section"
            aria-labelledby="faq-title"
        >
            <div className="faq-aside">
                <span className="kicker">FAQ</span>
                <h2 id="faq-title">常见问题与边界说明</h2>
                <p>
                    关于智能终端、代理兼容、SSH 凭据加密和存储迁移的具体限制，均可对照源码文档核验。
                </p>
                <div className="text-links" style={{ marginTop: "1rem" }}>
                    <a className="text-link" href={docs.issues}>
                        问题反馈 (GitHub Issues){" "}
                        <ArrowUpRight size={13} aria-hidden="true" />
                    </a>
                </div>
            </div>
            <div className="faq-list">
                {faqs.map(({ question, answer }) => (
                    <details key={question}>
                        <summary>{question}</summary>
                        <p>{answer}</p>
                    </details>
                ))}
            </div>
        </section>
    );
}
