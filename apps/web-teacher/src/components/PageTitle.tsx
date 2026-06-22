import type { ReactNode } from "react";
import { Flex, Typography } from "antd";

const { Text, Title } = Typography;

type PageTitleProps = {
  title: string;
  description?: string;
  extra?: ReactNode;
};

export function PageTitle({ title, description, extra }: PageTitleProps) {
  return (
    <Flex align="center" justify="space-between" gap={16} className="page-title">
      <div>
        <Title level={2}>{title}</Title>
        {description ? <Text type="secondary" className="page-title-description">{description}</Text> : null}
      </div>
      {extra}
    </Flex>
  );
}
