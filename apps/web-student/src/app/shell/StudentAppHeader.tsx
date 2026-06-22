import type { ReactNode } from "react";

export function StudentAppHeader({ title, subtitle, actions }: { title: string; subtitle: string; actions?: ReactNode }) {
  return (
    <header className={actions ? "student-app-header has-actions" : "student-app-header"}>
      <div>
        <p>{subtitle}</p>
        <h1>{title}</h1>
      </div>
      {actions}
    </header>
  );
}
