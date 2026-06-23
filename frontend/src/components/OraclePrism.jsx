import React from "react";

function OraclePrism({ className = "" }) {
  return (
    <div className={`prism-stage ${className}`.trim()} aria-hidden="true">
      <span className="circuit-line line-a" />
      <span className="circuit-line line-b" />
      <span className="circuit-line line-c" />
      <span className="circuit-line line-d" />
      <div className="prism-core">
        <span className="prism-face face-top" />
        <span className="prism-face face-bottom" />
        <span className="prism-face face-left" />
        <span className="prism-face face-right" />
      </div>
    </div>
  );
}

export default OraclePrism;
