"use client";

import { useEffect, useState } from "react";

export function TamperSample() {
  const [sample, setSample] = useState<"recorded" | "letter">("recorded");
  const [image, setImage] = useState<string | null>(null);
  const [fileName, setFileName] = useState("EDIT_0192 / RECORDED OUTPUT");
  useEffect(() => () => { if (image) URL.revokeObjectURL(image); }, [image]);

  function loadImage(file: File | undefined) {
    if (!file || !file.type.startsWith("image/")) return;
    setImage(URL.createObjectURL(file));
    setFileName(file.name.toUpperCase());
  }

  return (
    <div className="lab-workbench">
      <div className="workbench-bar"><span>DOCUMENT VIEWER / {fileName}</span><span>{image ? "LOCAL PREVIEW · NO INFERENCE" : sample === "recorded" ? "SAVED ASCFORMER SELF-TEST" : "PUBLIC-DOMAIN SCAN · NO INFERENCE"}</span></div>
      <div className="workbench-body">
        <div className="lab-document-stage">
          {image ? <div className="uploaded-document"><img src={image} alt="Your locally selected document preview; no prediction has been run" /></div> : <div className="real-document"><img src={sample === "recorded" ? "/tafe-id/recorded-edit-0192.png" : "/tafe-id/public-document.png"} alt={sample === "recorded" ? "Saved ASCFormer output on RTM edit_0192: a red predicted region near the top of the document" : "Public-domain handwritten letter from Wikimedia Commons"} /><small>{sample === "recorded" ? "Recorded self-test screenshot · edit_0192" : "Public-domain scan · Wikimedia Commons"}</small></div>}
        </div>
        <div className="lab-view-controls">
          <p className="lab-kicker">{image ? "LOCAL IMAGE PREVIEW" : sample === "recorded" ? "REAL MODEL OUTPUT / SAVED RUN" : "DOCUMENT VIEW / UNPROCESSED"}</p>
          <h3>{image ? "Your document stays here." : sample === "recorded" ? "A prediction you can inspect." : "A real archive scan."}</h3>
          <p>{image ? "This image stays in your browser. No model has processed it and no prediction is drawn. Use the Colab runbook below for actual inference." : sample === "recorded" ? "This is the saved output from our successful ASCFormer self-test on RTM edit_0192. The red region was produced by the reference model. Viewing it does not rerun inference, and it is not a ground-truth annotation." : "This handwritten letter is an unprocessed public-domain example. No tampering prediction is claimed for it."}</p>
          {!image && sample === "recorded" && <p className="lab-footnote">Recorded run: 1122 × 794 pixels · predicted region 0.279% of pixels · maximum model probability 0.969. These are output diagnostics, not accuracy scores.</p>}
          <div className="demo-actions"><label className="lab-button upload-button">Preview your image<span>＋</span><input type="file" accept="image/*" onChange={e => loadImage(e.target.files?.[0])} /></label><button type="button" className="lab-button" onClick={() => { setImage(null); setSample("recorded"); setFileName("EDIT_0192 / RECORDED OUTPUT"); }}>View recorded prediction ↗</button><button type="button" className="lab-button" onClick={() => { setImage(null); setSample("letter"); setFileName("PUBLIC ARCHIVE / LETTER"); }}>View unprocessed example ↗</button></div>
          <a className="lab-link demo-source" href="https://commons.wikimedia.org/wiki/File:Vishwanath_Datta%27s_handwritten_letter.png" target="_blank" rel="noreferrer">View image source and license ↗</a>
          <a className="lab-link demo-colab" href="https://colab.research.google.com/drive/12IhdcGGqjP305I_xVmGwICSyU9mMRByd" target="_blank" rel="noreferrer">Run the verified GPU demo in Colab ↗</a>
          <p className="lab-footnote">New predictions require a running Colab session. This website currently shows a recorded result and local previews; it does not host the model.</p>
        </div>
      </div>
    </div>
  );
}
