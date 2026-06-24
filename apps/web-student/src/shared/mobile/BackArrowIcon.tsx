import type { SVGProps } from "react";

export const studentBackArrowIconClassName = "student-back-arrow-icon";
export const studentBackArrowIconSize = 30;
export const studentBackArrowViewBox = "0 0 24 24";
export const studentBackArrowPath =
  "M7.414 13l5.043 5.04-1.414 1.42L3.586 12l7.457-7.46 1.414 1.42L7.414 11H21v2H7.414z";

function backArrowClassName(className?: string) {
  return [studentBackArrowIconClassName, className].filter(Boolean).join(" ");
}

export function BackArrowIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      className={backArrowClassName(className)}
      width={studentBackArrowIconSize}
      height={studentBackArrowIconSize}
      viewBox={studentBackArrowViewBox}
      fill="currentColor"
      aria-hidden="true"
      {...props}
    >
      <path d={studentBackArrowPath} />
    </svg>
  );
}

export function createBackArrowSvg(className?: string) {
  return `<svg class="${backArrowClassName(className)}" xmlns="http://www.w3.org/2000/svg" width="${studentBackArrowIconSize}" height="${studentBackArrowIconSize}" viewBox="${studentBackArrowViewBox}" fill="currentColor" aria-hidden="true"><path d="${studentBackArrowPath}"></path></svg>`;
}
