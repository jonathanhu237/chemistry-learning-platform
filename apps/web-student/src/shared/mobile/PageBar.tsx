import { ArrowLeft } from "lucide-react";
import { MobileIconButton } from "../../mobile/primitives";

export function PageBar({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <div className="pagebar">
      <MobileIconButton className="icon-action" type="button" onClick={onBack} aria-label="返回">
        <ArrowLeft size={18} />
      </MobileIconButton>
      <h2>{title}</h2>
    </div>
  );
}
