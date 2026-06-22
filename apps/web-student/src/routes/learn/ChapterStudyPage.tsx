import { useState } from "react";
import { useParams, useSearch } from "@tanstack/react-router";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { FamilyCatalogShell } from "./FamilyCatalogShell";

export function ChapterStudyPage() {
  const params = useParams({ strict: false }) as { profileId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const [title, setTitle] = useState("章节学习");
  const profileId = params.profileId || "";

  return (
    <DetailPageFrame title={title} source={search.from} className="family-detail-frame">
      <FamilyCatalogShell
        profileId={profileId}
        initialElementSymbol={search.elementSymbol}
        onTitleChange={setTitle}
      />
    </DetailPageFrame>
  );
}
