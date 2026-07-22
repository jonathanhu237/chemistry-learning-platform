import { useState } from "react";
import { App as AntApp, Badge, Button, Dropdown, Layout, Modal, Space, Typography } from "antd";
import { DownOutlined, KeyOutlined, LogoutOutlined, UserOutlined } from "@ant-design/icons";

import type { LoginResponse, User } from "../../api/auth";
import { PasswordChangeForm } from "../../features/account/PasswordChangeForm";

const { Header } = Layout;
const { Text } = Typography;

export function teacherRoleLabel(role: User["role"]) {
  if (role === "admin") return "主管教师";
  if (role === "teacher") return "教师";
  return "学生";
}

export function AdminHeader({
  user,
  onLogout,
  onSessionReplaced,
}: {
  user: User;
  onLogout: () => void;
  onSessionReplaced: (response: LoginResponse) => void;
}) {
  const { message } = AntApp.useApp();
  const [passwordOpen, setPasswordOpen] = useState(false);

  return (
    <Header className="admin-header">
      <div className="admin-header-left">
        <Space>
          <Badge status="success" />
          <Text>
            {user.display_name} · {teacherRoleLabel(user.role)}
          </Text>
        </Space>
      </div>
      <Dropdown
        trigger={["click"]}
        menu={{
          items: [
            { key: "identity", icon: <UserOutlined />, label: user.username, disabled: true },
            { key: "password", icon: <KeyOutlined />, label: "修改密码" },
            { type: "divider" },
            { key: "logout", icon: <LogoutOutlined />, label: "退出登录", danger: true },
          ],
          onClick: ({ key }) => {
            if (key === "password") setPasswordOpen(true);
            if (key === "logout") onLogout();
          },
        }}
      >
        <Button icon={<UserOutlined />}>
          账户 <DownOutlined />
        </Button>
      </Dropdown>
      <Modal title="修改密码" open={passwordOpen} footer={null} destroyOnHidden onCancel={() => setPasswordOpen(false)}>
        <Text type="secondary" className="account-modal-description">
          保存后将更新当前登录凭证，并让其他设备上的旧会话失效。
        </Text>
        <PasswordChangeForm
          onChanged={(response) => {
            onSessionReplaced(response);
            setPasswordOpen(false);
            message.success("密码已修改");
          }}
        />
      </Modal>
    </Header>
  );
}
