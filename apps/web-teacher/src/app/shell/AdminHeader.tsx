import { Badge, Button, Layout, Space, Typography } from "antd";
import { LogoutOutlined } from "@ant-design/icons";

import type { User } from "../../api/auth";

const { Header } = Layout;
const { Text } = Typography;

export function AdminHeader({ user, onLogout }: { user: User; onLogout: () => void }) {
  return (
    <Header className="admin-header">
      <div className="admin-header-left">
        <Space>
          <Badge status="success" />
          <Text>
            {user.display_name} · {user.role}
          </Text>
        </Space>
      </div>
      <Button icon={<LogoutOutlined />} onClick={onLogout}>
        退出
      </Button>
    </Header>
  );
}
