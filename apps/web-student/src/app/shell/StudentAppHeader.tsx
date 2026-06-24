import type { ReactNode } from "react";

type StudentAppHeaderProps = {
  title?: string;
  subtitle?: string;
  brand?: ReactNode;
  actions?: ReactNode;
  below?: ReactNode;
  ariaLabel?: string;
};

export function StudentAppHeader({ title, subtitle, brand, actions, below, ariaLabel }: StudentAppHeaderProps) {
  return (
    <header
      className={["student-app-header", brand ? "has-brand" : "", actions ? "has-actions" : "", below ? "has-below" : ""].filter(Boolean).join(" ")}
      aria-label={ariaLabel}
    >
      <div className="student-app-header-title-row">
        {brand ? (
          <div className="student-app-header-brand">{brand}</div>
        ) : (
          <div>
            <p>{subtitle}</p>
            <h1>{title}</h1>
          </div>
        )}
        {actions ? <div className="student-app-header-actions">{actions}</div> : null}
      </div>
      {below ? <div className="student-app-header-below">{below}</div> : null}
    </header>
  );
}
