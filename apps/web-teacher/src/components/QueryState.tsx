import type { ReactNode } from "react";
import { Alert, Empty, Spin } from "antd";

type QueryStateProps = {
  loading: boolean;
  error?: unknown;
  empty?: boolean;
  children: ReactNode;
};

function errorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return String(error || "未知错误");
}

export function QueryState({ loading, error, empty, children }: QueryStateProps) {
  if (loading) {
    return (
      <div className="center-panel">
        <Spin />
      </div>
    );
  }
  if (error) {
    return <Alert type="error" showIcon title="加载失败" description={errorMessage(error)} />;
  }
  if (empty) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" />;
  }
  return children;
}
