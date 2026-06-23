import React from "react";

function SignalBadge({ tone = "neutral", children }) {
  return <span className={`signal-badge ${tone}`}>{children}</span>;
}

export default SignalBadge;
