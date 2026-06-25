import React from "react";
import { BarChart3, BrainCircuit, LineChart, Target } from "lucide-react";

const links = [
  { href: "/dashboard", label: "Panel", icon: BarChart3 },
  { href: "/predict", label: "Predicción", icon: Target },
  { href: "/methodology", label: "Metodología", icon: BrainCircuit },
  { href: "/model", label: "Modelo", icon: LineChart },
];

function Navbar({ apiStatus, currentPath, onNavigate }) {
  return (
    <header className="navbar-shell">
      <a
        aria-label="El Oráculo de Capital Riesgo"
        className="brand-mark"
        href="/"
        onClick={(event) => onNavigate(event, "/")}
      >
        <span className="brand-glyph" aria-hidden="true">
          <span className="mini-prism" />
        </span>
        <span>
          <strong>El Oráculo</strong>
          <small>Señal. Inteligencia. Ventaja.</small>
        </span>
      </a>

      <nav className="nav-links" aria-label="Navegación principal">
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
