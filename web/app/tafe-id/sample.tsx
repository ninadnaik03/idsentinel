"use client";

import { useState } from "react";

export function TamperSample() {
  const [mask, setMask] = useState(true);
  const [image, setImage] = useState<string | null>(null);
  const [fileName, setFileName] = useState("SAMPLE / ARCHIVE 001");

  function loadImage(file: File | undefined) {
    if (!file) return;
    setImage(URL.createObjectURL(file));
    setFileName(file.name.toUpperCase());
    setMask(true);
  }

  return (
    <div className="lab-workbench">
      <div className="workbench-bar"><span>DOCUMENT VIEWER / {fileName}</span><span>{image ? "LOCAL PREVIEW · NO UPLOAD" : "PRELOADED PUBLIC-DOMAIN SCAN"}</span></div>
      <div className="workbench-body">
        <div className="lab-document-stage">
          {image ? <div className="uploaded-document"><img src={image} alt="Your locally selected document preview" />{mask && <span className="uploaded-overlay">ILLUSTRATIVE REGION</span>}</div> : <div className="real-document"><img src="/tafe-id/public-document.png" alt="Public-domain handwritten letter used as the preloaded demo image" />{mask && <span className="real-overlay">ILLUSTRATIVE REGION</span>}<small>Public-domain scan · Wikimedia Commons</small></div>}
        </div>
        <div className="lab-view-controls">
          <p className="lab-kicker">VIEW MODE / {mask ? "OVERLAY" : "DOCUMENT"}</p>
          <h3>{image ? "Preview your document." : "A real document scan."}<br />{image ? "Keep your file private." : "A closer inspection."}</h3>
          <p>{image ? "Your image is rendered in this browser only. This public page does not send it to a server or claim a model prediction." : "This preloaded scan is an actual public-domain document image. The highlighted region is a visual example of how a localization result is presented, not a recorded prediction for this letter."}</p>
          <div className="demo-actions"><label className="lab-button upload-button">Choose an image<span>＋</span><input type="file" accept="image/*" onChange={e => loadImage(e.target.files?.[0])} /></label><button type="button" className="lab-button" aria-pressed={mask} onClick={() => setMask(!mask)}>{mask ? "Hide example overlay" : "Show example overlay"}<span>{mask ? "−" : "+"}</span></button></div>
          <div className="viewer-key"><i /> ILLUSTRATIVE INSPECTION REGION</div>
          <a className="lab-link demo-source" href="https://commons.wikimedia.org/wiki/File:Vishwanath_Datta%27s_handwritten_letter.png" target="_blank" rel="noreferrer">View image source and license ↗</a>
          <a className="lab-link demo-colab" href="https://colab.research.google.com/drive/12IhdcGGqjP305I_xVmGwICSyU9mMRByd" target="_blank" rel="noreferrer">Run the verified GPU demo in Colab ↗</a>
          <p className="lab-footnote">The Colab notebook runs the actual checkpoint. This page is a privacy-safe interface demo; the overlay is illustrative.</p>
        </div>
      </div>
    </div>
  );
}
