import { useNavigate } from "@tanstack/react-router";
import { LearningEntryPanel } from "../../features/learning/LearningEntryPanel";
import { navigateToChapter, navigateToLearningArea } from "../../app/router/navigation";

export function LearnRootPage() {
  const navigate = useNavigate();
  return (
    <LearningEntryPanel
      onSelectArea={(areaId) => {
        navigateToLearningArea(navigate, areaId, { from: "learn" });
      }}
      onSelectProfile={(profile) => {
        navigateToChapter(navigate, profile.profile_id, { from: "learn" });
      }}
    />
  );
}
