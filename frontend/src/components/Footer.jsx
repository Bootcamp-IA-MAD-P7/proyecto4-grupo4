import React from "react";

const links = [
  { href: "/", label: "Inicio" },
  { href: "/dashboard", label: "Panel" },
  { href: "/predict", label: "Predicción" },
  { href: "/methodology", label: "Metodología" },
  { href: "/model", label: "Modelo" },
];

function Footer({ onNavigate }) {
  return (
    <footer className="footer">
      <a className="brand-mark footer-brand" href="/" onClick={(event) => onNavigate(event, "/")}>
        <span className="brand-glyph" aria-hidden="true">
          <span className="mini-prism" />
        </span>
        <span>
          <strong>El Oráculo de Capital Riesgo</strong>
          <small>Motor predictivo de valoración para análisis de startups.</small>
        </span>
      </a>

      <nav className="footer-links" aria-label="Navegación secundaria">
        {links.map((link) => (
          <a href={link.href} key={link.href} onClick={(event) => onNavigate(event, link.href)}>
            {link.label}
          </a>
        ))}
      </nav>
    </footer>
  );
}

export default Footer;
