import React from "react";

const footerSections = [
  {
    title: "Proyecto",
    items: ["Trabajo académico", "Grupo 4 · Bootcamp IA"],
  },
  {
    title: "Stack",
    items: ["React + Vite", "FastAPI · PostgreSQL · Docker"],
  },
  {
    title: "Uso responsable",
    items: ["Referencia predictiva", "Sin finalidad de asesoramiento financiero"],
  },
];

function Footer({ onNavigate }) {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-summary">
        <a className="brand-mark footer-brand" href="/" onClick={(event) => onNavigate(event, "/")}>
          <span className="brand-glyph" aria-hidden="true">
            <span className="mini-prism" />
          </span>
          <span>
            <strong>El Oráculo de Capital Riesgo</strong>
            <small>Motor predictivo de valoración para análisis de startups.</small>
          </span>
        </a>
        <p>© {currentYear} · Proyecto educativo de regresión lineal y despliegue web.</p>
      </div>

      <div className="footer-sections" aria-label="Información del proyecto">
        {footerSections.map((section) => (
          <section key={section.title}>
            <h2>{section.title}</h2>
            {section.items.map((item) => (
              <p key={item}>{item}</p>
            ))}
          </section>
        ))}
      </div>
    </footer>
  );
}

export default Footer;
