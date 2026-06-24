import {
  ButtonHTMLAttributes,
  forwardRef,
  InputHTMLAttributes,
  ReactNode,
  TextareaHTMLAttributes,
} from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

export function MobileButton({
  variant = "primary",
  fullWidth = true,
  loading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  fullWidth?: boolean;
  loading?: boolean;
}) {
  return (
    <button
      className={cx("mobile-button", `mobile-button--${variant}`, fullWidth && "mobile-button--full", className)}
      disabled={disabled || loading}
      {...props}
    >
      {children}
    </button>
  );
}

export function MobileIconButton({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={cx("mobile-icon-button", className)} {...props} />;
}

export function MobileField({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cx("mobile-field", className)} {...props} />;
}

export const MobileTextArea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(function MobileTextArea(
  { className, ...props },
  ref,
) {
  return <textarea ref={ref} className={cx("mobile-textarea", className)} {...props} />;
});

export function MobileStatus({
  icon,
  text,
  tone = "neutral",
  className,
}: {
  icon: ReactNode;
  text: ReactNode;
  tone?: "neutral" | "error" | "empty";
  className?: string;
}) {
  return (
    <div className={cx("mobile-status", `mobile-status--${tone}`, className)} aria-live={tone === "error" ? "assertive" : "polite"}>
      {icon}
      <span>{text}</span>
    </div>
  );
}

export function MobileEmptyState({
  icon,
  children,
  className,
}: {
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx("mobile-empty-state", className)}>
      {icon}
      {typeof children === "string" ? <span>{children}</span> : children}
    </div>
  );
}
