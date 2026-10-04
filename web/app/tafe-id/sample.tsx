"use client";

import { useState } from "react";

export function TamperSample() {
  const [showMask, setShowMask] = useState(true);

  return <div className="tafe-sample">
    <div className={`sample-document ${showMask ? "mask-on" : ""}`} aria-label="Illustrative document result showing a localized edit">
      <div className="sample-paper">
        <div className="sample-topline" />
        <div className="sample-title" />
        <div className="sample-rule" />
        <div className="sample-lines">
          <i/><i/><i/><i/><i/><i/><i/><i/><i/><i/>
        </div>
        <div className="sample-edit"><span>localized text edit</span></div>
        <div className="sample-lines lower"><i/><i/><i/><i/><i/><i/></div>
      </div>
    </div>
    <div className="sample-controls">
      <div><span className="sample-status">Verified inference format</span><h3>Pixel-level manipulation mask</h3><p>Toggle the mask to inspect how the interface separates the document from the predicted altered region. This visual is an interface illustration; the reported metrics below come from recorded model evaluation.</p></div>
      <button onClick={() => setShowMask(value => !value)} aria-pressed={showMask}>
        {showMask ? "Hide predicted mask" : "Show predicted mask"}
      </button>
    </div>
  </div>;
}
