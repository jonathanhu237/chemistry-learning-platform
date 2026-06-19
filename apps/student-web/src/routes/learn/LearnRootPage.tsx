import { useNavigate } from "@tanstack/react-router";
import { LearningEntryPanel } from "../../features/learning/LearningEntryPanel";
import { navigateToChapter } from "../../app/router/navigation";

export function LearnRootPage() {
  const navigate = useNavigate();
  return (
    <LearningEntryPanel
      onSelectProfile={(profile) => {
        navigateToChapter(navigate, profile.profile_id, { from: "learn" });
      }}
    />
  );
}
