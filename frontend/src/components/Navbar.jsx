import { BarChart3, BrainCircuit, LineChart, Target } from "lucide-react";

const links = [
  { href: "#dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "#predict", label: "Predicción", icon: Target },
  { href: "#methodology", label: "Metodología", icon: BrainCircuit },
  { href: "#model", label: "Modelo", icon: LineChart },
];

function Navbar({ apiStatus }) {
  return (
    <header className="navbar-shell">
      <a className="brand-mark" href="#top" aria-label="El Oráculo de Venture Capital">
        <span className="brand-glyph" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span>
          <strong>El Oráculo VC</strong>
          <small>Señal. Inteligencia. Ventaja.</small>
        </span>
      </a>

      <nav className="nav-links" aria-label="Navegacion principal">
        {links.map(({ href, label, icon: Icon }) => (
          <a key={href} href={href}>
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
