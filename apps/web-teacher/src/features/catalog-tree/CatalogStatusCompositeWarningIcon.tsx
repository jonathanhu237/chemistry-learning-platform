import type { CSSProperties } from "react";
import { FileText, TriangleAlert, Video } from "lucide-react";

type CatalogStatusCompositeWarningIconProps = {
  kind: "content" | "video";
  size?: number;
  strokeWidth?: number;
};

export function CatalogStatusCompositeWarningIcon({
  kind,
  size = 16,
  strokeWidth = 1.9,
}: CatalogStatusCompositeWarningIconProps) {
  const SubjectIcon = kind === "video" ? Video : FileText;
  const markerSize = Math.max(10, Math.round(size * 0.72));
  const style = {
    "--catalog-status-composite-size": `${size}px`,
    "--catalog-status-composite-marker-size": `${markerSize}px`,
  } as CSSProperties;

  return (
    <span
      aria-hidden="true"
      className={`catalog-composite-warning-icon is-${kind}`}
      style={style}
    >
      <SubjectIcon
        className="catalog-composite-warning-icon-subject"
        size={size}
        strokeWidth={strokeWidth}
      />
      <TriangleAlert
        className="catalog-composite-warning-icon-alert"
        size={markerSize}
        strokeWidth={strokeWidth}
      />
    </span>
  );
}
