import type { ReactNode } from "react";
import { MobileStatus } from "../../mobile/primitives";

export function LearningState({ icon, text }: { icon: ReactNode; text: string }) {
  return <MobileStatus className="learning-state" icon={icon} text={text} />;
}
