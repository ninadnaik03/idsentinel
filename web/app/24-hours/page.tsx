import { PageHero, Shell } from "../components";
export const metadata={title:"24-Hour Build Story"};
const steps=[
 ["00","Paper + feasibility audit","Separated paper-described components from implementation choices before writing model code.","Scope locked"],
 ["01","Dataset provenance audit","Found the proposed composite benchmark was source-confounded and treated it as a blocker.","Four-class merge rejected"],
 ["02","Protocol A-Reduced","Streamed only selected frames, preserved lineage, and produced a balanced 300-sample protocol.","214 / 42 / 44"],
 ["03","Making it work on 8 GB","Serial decoding, local batch 1, zero workers, no RAM cache, CPU extraction, temporary free T4 training.","~573 MiB extraction peak"],
 ["04","Finding the signal","RetinaFace with CLAHE and Haar fallbacks generated 300 context-preserving 384×384 crops.","300 / 300 crops"],
 ["05","Start simple: semantics","ConvNeXt-Tiny established a controlled semantic baseline.","0.590 Macro-F1"],
 ["06","What if texture helps?","A 64-D pixel-only texture path lifted PRINT F1 from .690 to .889.","0.679 Macro-F1"],
 ["07","What do edges add?","Fixed Sobel gradients added different corrections, but SCREEN F1 fell in this run.","0.640 Macro-F1"],
 ["08","Three experiments, one split","Compared aggregate metrics and failure transitions without test-set retuning.","5 failures persisted"],
 ["09","Analysis + publication","Published safe code and aggregate evidence while excluding restricted document imagery.","Open research record"]
];
export default function Story(){return <Shell><PageHero kicker="From paper audit to public record" title="What 24 hours actually told us." copy="The sprint was less about chasing a score than making defensible decisions under dataset, storage, compute, and time constraints."/><div className="content"><section className="timeline">{steps.map(s=><article key={s[0]}><small>{s[0]}</small><h3>{s[1]}</h3><p>{s[2]}</p><strong>{s[3]}</strong></article>)}</section><section><h2>Lessons, not slogans</h2><div className="card-grid"><article className="card"><h3>Data first</h3><p>A scientifically clean protocol mattered more than immediate training.</p></article><article className="card"><h3>Branches shift failures</h3><p>Texture and edge changed which samples failed—not simply how many.</p></article><article className="card"><h3>Small data = humility</h3><p>Forty-four test samples cannot support broad performance claims.</p></article></div></section></div></Shell>}
