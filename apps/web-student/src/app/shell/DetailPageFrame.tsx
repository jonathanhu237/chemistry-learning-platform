import type { ReactNode } from "react";
import { PageBar } from "../../shared/mobile/PageBar";
import { useDetailBack } from "./useDetailBack";

export function DetailPageFrame({
  title,
  source,
  actions,
  className,
  children,
}: {
  title: string;
  source?: string | null;
  actions?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  const goBack = useDetailBack(source);
  return (
    <section className={className ? `detail-page-frame ${className}` : "detail-page-frame"}>
      <PageBar title={title} onBack={goBack} />
      {actions ? <div className="student-app-header-actions detail-page-actions">{actions}</div> : null}
      {children}
    </section>
  );
}
