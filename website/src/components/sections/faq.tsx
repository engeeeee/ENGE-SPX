import { faqs } from "@/lib/content";

export function FaqSection() {
    return (
        <section id="faq" className="section container faq-section" aria-labelledby="faq-title">
            <h2 id="faq-title">常见问题</h2>
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
