import { useEffect, useId } from "react";
import {
  autoUpdate,
  flip,
  FloatingFocusManager,
  FloatingPortal,
  offset,
  shift,
  size,
  useDismiss,
  useFloating,
  useInteractions,
  useRole,
} from "@floating-ui/react";
import { BookOpenCheck } from "lucide-react";
import type { StudentLearningPageResponse } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { periodicLegendLabelByAreaId, type AreaId } from "../periodic-table/periodicHelpers";
import { LearningChapterEntryRows, learningProfilesForArea } from "./LearningAreaChapterList";

type LearningProfileSummary = StudentLearningPageResponse["profiles"][number];

export function LearningAreaPopover({
  selectedArea,
  anchorElement,
  open,
  profiles,
  onOpenChange,
  onSelectProfile,
}: {
  selectedArea: AreaId | null;
  anchorElement: HTMLElement | null;
  open: boolean;
  profiles: LearningProfileSummary[];
  onOpenChange: (open: boolean) => void;
  onSelectProfile: (profile: LearningProfileSummary) => void;
}) {
  const titleId = useId();
  const selectedAreaProfiles = selectedArea ? learningProfilesForArea(selectedArea, profiles) : [];
  const { refs, floatingStyles, context } = useFloating({
    open,
    onOpenChange,
    placement: "bottom-start",
    strategy: "fixed",
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(8),
      flip({ padding: 12 }),
      shift({ padding: 12 }),
      size({
        padding: 12,
        apply({ availableHeight, elements }) {
          const maxHeight = Math.max(120, Math.min(availableHeight, 460));
          elements.floating.style.setProperty("--learning-area-popover-max-height", `${maxHeight}px`);
        },
      }),
    ],
  });
  const dismiss = useDismiss(context, { escapeKey: true, outsidePress: false });
  const role = useRole(context, { role: "dialog" });
  const { getFloatingProps } = useInteractions([dismiss, role]);

  useEffect(() => {
    refs.setReference(anchorElement);
  }, [anchorElement, refs]);

  if (!open || !selectedArea || !anchorElement) return null;

  return (
    <FloatingPortal>
      <div
        aria-hidden="true"
        className="learning-area-popover-backdrop"
        onPointerDown={(event) => {
          event.preventDefault();
          event.stopPropagation();
          onOpenChange(false);
        }}
      />
      <FloatingFocusManager context={context} initialFocus={-1} modal={false} returnFocus={false}>
        <section
          ref={refs.setFloating}
          className="learning-area-popover"
          style={floatingStyles}
          {...getFloatingProps({
            "aria-labelledby": titleId,
          })}
        >
          <div className="learning-area-popover-head">
            <p>选择章节</p>
            <h3 id={titleId}>{periodicLegendLabelByAreaId[selectedArea]}</h3>
          </div>
          {selectedAreaProfiles.length ? (
            <LearningChapterEntryRows
              profiles={selectedAreaProfiles}
              onSelectProfile={(profile) => {
                onOpenChange(false);
                onSelectProfile(profile);
              }}
            />
          ) : (
            <MobileEmptyState className="empty-learning-card learning-area-popover-empty" icon={<BookOpenCheck size={20} />}>
              <span>暂无可学习章节</span>
            </MobileEmptyState>
          )}
        </section>
      </FloatingFocusManager>
    </FloatingPortal>
  );
}
