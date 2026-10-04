import type { Metadata } from "next";
import Link from "next/link";
import { Eyebrow, Shell } from "../components";
import { TamperSample } from "./sample";

export const metadata: Metadata = {
  title: "TAFE-ID | Text Manipulation Localization",
  description: "A verified RTM/ASCFormer document-tampering localization project with reproducible metrics, sample interaction and an honest implementation record.",
};

const metrics = [
  ["0.844", "Precision"], ["0.493", "Recall"], ["0.623", "F1"], ["0.452", "IoU"],
];

const categories = [
  ["Splice", .8826], ["Cover", .8601], ["CPMV", .8212], ["Edit", .7935], ["Insert", .2336], ["Inpaint", .1545],
];

export default function TafeIdPage() {
  return <Shell>
    <section className="tafe-hero">
      <div className="tafe-hero-copy">
        <Eyebrow>RTM document forensics · verified reference inference</Eyebrow>
        <h1>Locate the edit.<br/><span>Show the evidence.</span></h1>
        <p className="lede">TAFE-ID localizes manipulated text and regions in document images. The public result is grounded in the authors&apos; released ASCFormer checkpoint, an audited RTM pipeline, and a reproducible CUDA environment.</p>
        <div className="actions">
          <a className="primary" href="#sample">Try the sample result</a>
          <a className="secondary" href="#reproduce">Reproduce the run</a>
        </div>
        <p className="hero-disclaimer">Research prototype · pixel localization · no production claim</p>
      </div>
      <div className="tafe-signal" aria-label="TAFE-ID processing overview">
        <div className="signal-doc"><i/><i/><i/><i/><span/></div>
        <div className="signal-path"><b>RGB</b><b>JPEG / DCT</b><b>FUSION</b></div>
        <div className="signal-mask"><span>MASK</span></div>
      </div>
    </section>

    <section className="tafe-metrics">
      {metrics.map(([value, label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}
      <p>Recorded on a fixed 32-document RTM held-out verification subset. These are project verification results, not the complete paper benchmark.</p>
    </section>

    <section className="section tafe-note">
      <Eyebrow>A note to Team HyperVerge</Eyebrow>
      <h2>Built after my technical interview.</h2>
      <p>After my technical interview with HyperVerge, I wanted to keep exploring the problem rather than stop at the conversation. I built TAFE-ID to understand document-forgery localization end to end: data integrity, frequency evidence, segmentation failure modes, reproducible inference, and the gap between a convincing demo and a defensible result.</p>
      <p>The strongest lesson was simple: a working forensic system is not the experiment with the longest training run. It is the one whose data, checkpoint, evaluation and limitations can all be inspected.</p>
    </section>

    <section className="section" id="sample">
      <div className="split"><div><Eyebrow>Interactive sample</Eyebrow><h2>See how a localized result is presented.</h2></div><p>The model returns a mask aligned to the source document. In the tested self-check, the released checkpoint found a small edited text region with a maximum manipulation probability of 0.969.</p></div>
      <TamperSample/>
    </section>

    <section className="section panel">
      <Eyebrow>What runs under the hood</Eyebrow>
      <div className="split"><h2>Appearance and frequency evidence meet at the pixel.</h2><p>ASCFormer combines visual structure with JPEG-domain forensic cues, fuses evidence across multiple scales, and produces a dense manipulation map. The pipeline was verified with strict checkpoint loading and live CUDA operator tests.</p></div>
      <div className="tafe-flow">
        <article><span>01</span><h3>Document image</h3><p>RGB appearance, layout and local text structure.</p></article>
        <article><span>02</span><h3>JPEG evidence</h3><p>DCT coefficients and quantization information expose compression inconsistencies.</p></article>
        <article><span>03</span><h3>Cross-attention fusion</h3><p>Multi-scale branches exchange complementary evidence.</p></article>
        <article><span>04</span><h3>Dense mask</h3><p>Every pixel receives a predicted manipulation label.</p></article>
      </div>
    </section>

    <section className="section">
      <div className="split"><div><Eyebrow>Held-out behavior</Eyebrow><h2>Strong on several edit families. Weak on subtle synthesis.</h2><p>Aggregate precision is high, but performance varies sharply by manipulation type. Inpaint and insert remain difficult. Clean documents contain no positive pixels, so positive-class pixel F1 is not meaningful for that category.</p></div><div className="category-bars">{categories.map(([name, score]) => <div key={name as string}><span>{name}</span><i><b style={{width: `${Number(score) * 100}%`}}/></i><strong>{Number(score).toFixed(3)}</strong></div>)}</div></div>
    </section>

    <section className="section tafe-truth">
      <Eyebrow>Research record</Eyebrow>
      <h2>The failed branch is part of the result.</h2>
      <div className="truth-grid">
        <article><strong>9,000</strong><span>RTM images and aligned masks audited</span></article>
        <article><strong>500</strong><span>custom frequency-pilot updates completed</span></article>
        <article><strong>0.000</strong><span>held-out F1 for the rejected custom pilot</span></article>
        <article><strong>0.623</strong><span>held-out F1 from the verified released model</span></article>
      </div>
      <p className="research-callout">The custom TAFE frequency model learned four fixed crops but collapsed to background predictions on held-out documents. It was rejected rather than presented as a success. The usable system therefore ships the authors&apos; released ASCFormer checkpoint, with that distinction kept explicit.</p>
    </section>

    <section className="section" id="reproduce">
      <div className="split"><div><Eyebrow>Reproducibility</Eyebrow><h2>One verified package. Exact environment.</h2></div><div><p>The archived deliverable contains the pinned source, official checkpoint, demo, deterministic self-test, environment lock and verification metrics. Dataset files are excluded because of size.</p><dl className="tafe-manifest"><div><dt>Python</dt><dd>3.8.20</dd></div><div><dt>PyTorch</dt><dd>2.0.0 + CUDA 11.8</dd></div><div><dt>MMCV</dt><dd>2.0.0</dd></div><div><dt>Checkpoint</dt><dd>Strict load passed</dd></div><div><dt>Package SHA-256</dt><dd>d69041eb…fe39a49</dd></div></dl></div></div>
    </section>

    <section className="section cta">
      <Eyebrow>Independent research implementation</Eyebrow>
      <h2>Useful because the limits are visible.</h2>
      <p>TAFE-ID demonstrates a working forensic inference pipeline. It does not claim a newly trained state-of-the-art model, a complete paper reproduction, or production readiness.</p>
      <div className="actions centered"><Link className="primary" href="/methodology">Read the methodology</Link><a className="secondary" href="https://github.com/ninadnaik03/idsentinel">Inspect the source ↗</a></div>
    </section>
  </Shell>;
}
