import type { ReactNode } from "react";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  ConfigProvider,
  Empty,
  Form,
  Input,
  Layout,
  Modal,
  Select,
  Spin,
  Switch,
  theme,
  Tooltip,
  type AlertProps,
  type ButtonProps,
  type CardProps,
  type ModalProps,
  type SelectProps,
  type SwitchProps,
  type TooltipProps,
} from "antd";
import type { FormProps, InputProps } from "antd";

function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

export function TeacherUiProvider({ children }: { children: ReactNode }) {
  return (
    <ConfigProvider
      componentSize="middle"
      theme={{
        algorithm: theme.compactAlgorithm,
        token: {
          colorPrimary: "#840006",
          colorInfo: "#840006",
          colorSuccess: "#0f766e",
          colorWarning: "#9b6500",
          colorError: "#a01318",
          colorText: "#171313",
          colorTextSecondary: "#675858",
          colorBorder: "#ead9d6",
          colorBgBase: "#f4eee9",
          colorBgContainer: "#fffdfb",
          borderRadius: 4,
          borderRadiusLG: 4,
          borderRadiusSM: 2,
          fontFamily: "'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', system-ui, sans-serif",
          controlHeight: 36,
          wireframe: false,
        },
        components: {
          Button: {
            borderRadius: 0,
            controlHeight: 38,
            fontWeight: 800,
          },
          Card: {
            borderRadiusLG: 4,
            headerBg: "#fffdfb",
          },
          Input: {
            borderRadius: 0,
            controlHeight: 38,
          },
          Select: {
            borderRadius: 0,
            controlHeight: 38,
          },
          Modal: {
            borderRadiusLG: 4,
          },
        },
      }}
    >
      <AntApp>{children}</AntApp>
    </ConfigProvider>
  );
}

export function TeacherShell({ children, testId }: { children: ReactNode; testId?: string }) {
  return (
    <Layout className="legacy-teacher-shell teacher-ui-shell" data-testid={testId}>
      {children}
    </Layout>
  );
}

export function TeacherSidebar({ children }: { children: ReactNode }) {
  return <Layout.Sider className="legacy-sidebar teacher-ui-sidebar" width={252}>{children}</Layout.Sider>;
}

export function TeacherMain({ children }: { children: ReactNode }) {
  return <Layout className="legacy-teacher-main teacher-ui-main">{children}</Layout>;
}

export function TeacherHeader({ children }: { children: ReactNode }) {
  return <Layout.Header className="legacy-teacher-header teacher-ui-header">{children}</Layout.Header>;
}

export function TeacherContent({ children }: { children: ReactNode }) {
  return <Layout.Content className="teacher-ui-content">{children}</Layout.Content>;
}

export function TeacherButton({ autoInsertSpace = false, className, ...props }: ButtonProps) {
  return <Button autoInsertSpace={autoInsertSpace} className={cx("teacher-ui-button", className)} {...props} />;
}

export function TeacherCard({ className, children, ...props }: CardProps) {
  return (
    <Card className={cx("teacher-ui-card", className)} {...props}>
      {children}
    </Card>
  );
}

export function TeacherPage({
  children,
  testId,
  className,
}: {
  children: ReactNode;
  testId?: string;
  className?: string;
}) {
  return (
    <main className={cx("legacy-teacher-page", "teacher-ui-page", className)} data-testid={testId}>
      {children}
    </main>
  );
}

export function TeacherAlert({ className, message, title, ...props }: AlertProps) {
  return <Alert className={cx("teacher-ui-alert", className)} showIcon title={title ?? message} {...props} />;
}

export function TeacherLoadingState({ message = "正在读取数据..." }: { message?: string }) {
  return (
    <div className="legacy-empty teacher-ui-state">
      <Spin size="small" />
      <span>{message}</span>
    </div>
  );
}

export function TeacherEmptyState({ message, compact = false }: { message: string; compact?: boolean }) {
  return (
    <div className={cx("legacy-empty", compact && "compact", "teacher-ui-empty")}>
      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={message} />
    </div>
  );
}

export function TeacherMetricGrid({ metrics }: { metrics: Array<{ label: string; value: ReactNode; unit?: string; description?: string }> }) {
  return (
    <div className="legacy-metric-grid teacher-ui-metric-grid">
      {metrics.map((metric) => (
        <TeacherCard className="legacy-metric teacher-ui-metric" key={metric.label}>
          <span>{metric.label}</span>
          <strong>
            {metric.value}
            {metric.unit ? <em>{metric.unit}</em> : null}
          </strong>
          {metric.description ? <small>{metric.description}</small> : null}
        </TeacherCard>
      ))}
    </div>
  );
}

export function TeacherModal({ className, ...props }: ModalProps) {
  return <Modal className={cx("teacher-ui-modal", className)} {...props} />;
}

export const TeacherForm = Form;
export type TeacherFormProps<T = unknown> = FormProps<T>;
export const TeacherInput = Input;
export type TeacherInputProps = InputProps;
export function TeacherSelect({ className, ...props }: SelectProps) {
  return <Select className={cx("teacher-ui-select", className)} {...props} />;
}
export type TeacherSelectProps = SelectProps;
export const TeacherSwitch = Switch;
export type TeacherSwitchProps = SwitchProps;
export const TeacherTooltip = Tooltip;
export type TeacherTooltipProps = TooltipProps;
