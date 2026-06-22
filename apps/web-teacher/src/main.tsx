import React from "react";
import ReactDOM from "react-dom/client";
import { AdminApp } from "./app/AdminApp";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("app") as HTMLElement).render(
  <React.StrictMode>
    <AdminApp />
  </React.StrictMode>,
);
