import { forwardRef, type ComponentPropsWithoutRef, type CSSProperties } from "react";

// Adapted from Magic UI's Shiny/Pulsating button patterns (MIT):
// https://magicui.design/docs/components/shiny-button
// https://magicui.design/docs/components/pulsating-button
const cx = (...classNames: Array<string | false | null | undefined>) =>
  classNames.filter(Boolean).join(" ");

export interface AIGlowButtonProps extends ComponentPropsWithoutRef<"button"> {
  borderRadius?: string;
  background?: string;
  glowColor?: string;
  glowSoftColor?: string;
  washColor?: string;
  washSoftColor?: string;
}

export const AIGlowButton = forwardRef<HTMLButtonElement, AIGlowButtonProps>(
  (
    {
      borderRadius = "100px",
      background = "linear-gradient(135deg, #004c28 0%, #06753e 48%, #139653 100%)",
      glowColor = "rgba(183, 255, 211, 0.42)",
      glowSoftColor = "rgba(72, 211, 126, 0.2)",
      washColor = "rgba(183, 255, 210, 0.5)",
      washSoftColor = "rgba(72, 211, 126, 0.24)",
      className,
      children,
      style,
      ...props
    },
    ref,
  ) => (
    <button
      ref={ref}
      className={cx("ai-glow-button", className)}
      style={
        {
          "--ai-glow-radius": borderRadius,
          "--ai-glow-bg": background,
          "--ai-glow-color": glowColor,
          "--ai-glow-soft-color": glowSoftColor,
          "--ai-wash-color": washColor,
          "--ai-wash-soft-color": washSoftColor,
          ...style,
        } as CSSProperties
      }
      {...props}
    >
      <span className="ai-glow-button__backlight" aria-hidden="true" />
      <span className="ai-glow-button__clip" aria-hidden="true">
        <span className="ai-glow-button__surface" />
        <span className="ai-glow-button__aura">
          <span className="ai-glow-button__blob ai-glow-button__blob-1" />
          <span className="ai-glow-button__blob ai-glow-button__blob-2" />
          <span className="ai-glow-button__blob ai-glow-button__blob-3" />
          <span className="ai-glow-button__blob ai-glow-button__blob-4" />
        </span>
        <span className="ai-glow-button__core" />
        <span className="ai-glow-button__wash" />
      </span>
      <span className="ai-glow-button__content">{children}</span>
    </button>
  ),
);

AIGlowButton.displayName = "AIGlowButton";
