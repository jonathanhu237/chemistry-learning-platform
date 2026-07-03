import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { LegacyTeacherApp } from "./LegacyTeacherApp";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <LegacyTeacherApp />
  </StrictMode>,
);
