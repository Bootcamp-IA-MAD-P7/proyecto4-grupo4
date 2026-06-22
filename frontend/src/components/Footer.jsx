import React from "react";

const links = [
  { href: "/", label: "Inicio" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/predict", label: "Prediccion" },
  { href: "/methodology", label: "Metodologia" },
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
          <strong>El Oraculo de Venture Capital</strong>
          <small>Motor predictivo de valoracion para analisis de startups.</small>
        </span>
      </a>

      <nav className="footer-links" aria-label="Navegacion secundaria">
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
