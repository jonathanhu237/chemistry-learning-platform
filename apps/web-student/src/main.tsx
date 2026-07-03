import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { LegacyStudentApp } from "./LegacyStudentApp";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <LegacyStudentApp />
  </StrictMode>,
);
