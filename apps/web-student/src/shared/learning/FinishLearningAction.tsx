import { GraduationCap, LoaderCircle } from "lucide-react";
import { MobileButton } from "../../mobile/primitives";

export function FinishLearningAction({ loading, error, onClick }: { loading: boolean; error: string; onClick: () => void }) {
  return (
    <section className="finish-learning">
      {error ? <div className="form-error">{error}</div> : null}
      <MobileButton variant="secondary" className="secondary-action finish-action" type="button" loading={loading} onClick={onClick}>
        {loading ? <LoaderCircle className="spin" size={18} /> : <GraduationCap size={18} />}
        <span>{loading ? "正在生成后测" : "完成学习"}</span>
      </MobileButton>
    </section>
  );
}
