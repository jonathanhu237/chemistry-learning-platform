import { MobileIconButton } from "../../mobile/primitives";
import { BackArrowIcon } from "./BackArrowIcon";

export function PageBar({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <div className="pagebar">
      <MobileIconButton className="icon-action" type="button" onClick={onBack} aria-label="返回">
        <BackArrowIcon />
      </MobileIconButton>
      <h2>{title}</h2>
    </div>
  );
}
