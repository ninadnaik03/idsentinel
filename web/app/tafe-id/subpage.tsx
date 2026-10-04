import type { ReactNode } from "react";

const links = [["/tafe-id", "Home"], ["/tafe-id/architecture", "Architecture"], ["/tafe-id/methodology", "Methodology"], ["/tafe-id/fine-tuning", "Fine-tuning"], ["/tafe-id/failures", "Failures"], ["/tafe-id/demo", "Demo"], ["/tafe-id/about", "About"]];

export function LabSubpage({ kicker, title, intro, children }: { kicker: string; title: ReactNode; intro: string; children: ReactNode }) {
  return <div className="tafe-lab"><header className="lab-header"><a className="lab-brand" href="/tafe-id"><span className="lab-emblem">T<span>+</span></span>TAFE-ID<small>FORENSICS LAB</small></a><nav aria-label="TAFE-ID navigation">{links.map(([href, label]) => <a href={href} key={href}>{label}</a>)}</nav><a className="lab-header-cta" href="https://doi.org/10.1016/j.patcog.2024.110828" target="_blank" rel="noreferrer">Paper ↗</a></header><main><section className="lab-width lab-sub-hero"><p className="lab-kicker">{kicker}</p><h1>{title}</h1><p className="lab-intro">{intro}</p></section><div className="lab-width lab-sub-content">{children}</div></main><footer className="lab-footer lab-width"><a className="lab-portfolio-link" href="https://ninadnaik.dev">← Ninad Naik / Portfolio</a><a className="lab-brand" href="/tafe-id">TAFE-ID<span className="lab-footer-cross">+</span></a><p>Document forensics, with an inspectable research record.</p><a href="/tafe-id">Back to TAFE-ID ↑</a></footer></div>;
}

export function LabSection({ label, title, children }: { label: string; title: string; children: ReactNode }) {
  return <section className="lab-sub-section"><p className="lab-kicker">{label}</p><h2>{title}</h2>{children}</section>;
}

export function LabCard({ label, title, children }: { label: string; title: string; children: ReactNode }) {
  return <article className="lab-sub-card"><span>{label}</span><h3>{title}</h3>{children}</article>;
}
