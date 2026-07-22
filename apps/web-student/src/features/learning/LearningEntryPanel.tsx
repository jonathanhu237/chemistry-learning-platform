import { useEffect, useState } from "react";
import { FlaskConical, LoaderCircle } from "lucide-react";
import { StudentLearningPageResponse, errorMessage, getStudentLearningPage } from "../../api";
import { LearningState } from "../../shared/mobile/LearningState";
import { PeriodicTable } from "../periodic-table/PeriodicTable";
import { periodicAreaIdForElement, periodicMetaForElement, profileAreaIds, type AreaId } from "../periodic-table/periodicHelpers";
import type { PeriodicElementSearchMeta } from "../periodic-table/periodicSearch";
import { LearningAreaPopover } from "./LearningAreaPopover";

type LearningProfileSummary = StudentLearningPageResponse["profiles"][number];
type LearningProfileSelectOptions = { elementSymbol?: string };

function profileContainsElement(profile: LearningProfileSummary, symbol: string): boolean {
  return profile.element_symbols.some((item) => item.toLowerCase() === symbol.toLowerCase());
}

function profileSharesElementGroup(profile: LearningProfileSummary, element: PeriodicElementSearchMeta): boolean {
  const elementArea = periodicAreaIdForElement(element);
  return profile.element_symbols.some((symbol) => {
    const profileElement = periodicMetaForElement(symbol);
    return Boolean(profileElement && profileElement.group === element.group && periodicAreaIdForElement(profileElement) === elementArea);
  });
}

function findProfileForElement(element: PeriodicElementSearchMeta, profiles: LearningProfileSummary[]): LearningProfileSummary | null {
  const exactProfile = profiles.find((profile) => profileContainsElement(profile, element.symbol));
  if (exactProfile) return exactProfile;

  const groupProfile = profiles.find((profile) => profileSharesElementGroup(profile, element));
  if (groupProfile) return groupProfile;

  const areaId = periodicAreaIdForElement(element);
  const canUseAreaFallback = areaId !== "p" && areaId !== "hydrogen";
  if (!canUseAreaFallback) return null;

  const areaProfiles = profiles.filter((profile) => profileAreaIds(profile).includes(areaId));
  return areaProfiles.length === 1 ? areaProfiles[0] : null;
}

export function LearningEntryPanel({
  onSelectProfile,
}: {
  onSelectProfile: (profile: LearningProfileSummary, options?: LearningProfileSelectOptions) => void;
}) {
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedArea, setSelectedArea] = useState<AreaId | null>(null);
  const [areaAnchorElement, setAreaAnchorElement] = useState<HTMLElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentLearningPage(null)
      .then((payload) => {
        if (!cancelled) setPage(payload);
      })
      .catch((requestError) => {
        if (!cancelled) setError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const profiles = page?.profiles || [];
  const closeAreaPopover = () => {
    setSelectedArea(null);
    setAreaAnchorElement(null);
  };
  const selectElementProfile = (element: PeriodicElementSearchMeta) => {
    const profile = findProfileForElement(element, profiles);
    if (!profile) return false;
    closeAreaPopover();
    onSelectProfile(profile, { elementSymbol: element.symbol });
    return true;
  };

  return (
    <section className="learning-panel learning-entry-panel" aria-label="元素周期表章节入口">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载学习章节" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {!loading && !error ? (
        <>
          <PeriodicTable
            onSelectArea={(areaId, triggerElement) => {
              if (selectedArea === areaId && areaAnchorElement === triggerElement) {
                closeAreaPopover();
                return;
              }
              setSelectedArea(areaId);
              setAreaAnchorElement(triggerElement);
            }}
            onSelectElement={(element) => selectElementProfile(element)}
          />
          <LearningAreaPopover
            selectedArea={selectedArea}
            anchorElement={areaAnchorElement}
            open={Boolean(selectedArea && areaAnchorElement)}
            profiles={profiles}
            onOpenChange={(isOpen) => {
              if (!isOpen) closeAreaPopover();
            }}
            onSelectProfile={onSelectProfile}
          />
        </>
      ) : null}
    </section>
  );
}
