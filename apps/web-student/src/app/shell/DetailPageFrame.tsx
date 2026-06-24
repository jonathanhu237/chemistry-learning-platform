import type { ReactNode } from "react";
import { PageBar } from "../../shared/mobile/PageBar";
import { useDetailBack } from "./useDetailBack";

export function DetailPageFrame({
  title,
  source,
  actions,
  className,
  onBack,
  children,
}: {
  title: string;
  source?: string | null;
  actions?: ReactNode;
  className?: string;
  onBack?: () => void;
  children: ReactNode;
}) {
  const goBack = useDetailBack(source);
  return (
    <section className={className ? `detail-page-frame ${className}` : "detail-page-frame"}>
      <PageBar title={title} onBack={onBack || goBack} />
      {actions ? <div className="student-app-header-actions detail-page-actions">{actions}</div> : null}
      {children}
    </section>
  );
}
