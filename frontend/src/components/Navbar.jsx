import React from "react";
import { BarChart3, BrainCircuit, LineChart, Target } from "lucide-react";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/predict", label: "Prediccion", icon: Target },
  { href: "/methodology", label: "Metodologia", icon: BrainCircuit },
  { href: "/model", label: "Modelo", icon: LineChart },
];

function Navbar({ apiStatus, currentPath, onNavigate }) {
  return (
    <header className="navbar-shell">
      <a
        aria-label="El Oraculo de Venture Capital"
        className="brand-mark"
        href="/"
        onClick={(event) => onNavigate(event, "/")}
      >
        <span className="brand-glyph" aria-hidden="true">
          <span className="mini-prism" />
        </span>
        <span>
          <strong>El Oraculo VC</strong>
          <small>Senal. Inteligencia. Ventaja.</small>
        </span>
      </a>

      <nav className="nav-links" aria-label="Navegacion principal">
        {links.map(({ href, label, icon: Icon }) => (
          <a
            className={currentPath === href ? "active" : ""}
            href={href}
            key={href}
            onClick={(event) => onNavigate(event, href)}
          >
            <Icon size={16} aria-hidden="true" />
            {label}
          </a>
        ))}
      </nav>

      <span className="api-pill">{apiStatus}</span>
    </header>
  );
}

export default Navbar;
