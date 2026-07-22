import { App as AntApp, Button, Card, Space, Typography } from "antd";
import { LogoutOutlined } from "@ant-design/icons";

import type { LoginResponse, User } from "../../api/auth";
import { PasswordChangeForm } from "./PasswordChangeForm";
import "./account.css";

const { Text, Title } = Typography;
const sysuLogoSrc = `${import.meta.env.BASE_URL}sysu-logo.svg`;

export function ForcedPasswordChangePage({
  user,
  onChanged,
  onLogout,
}: {
  user: User;
  onChanged: (response: LoginResponse) => void;
  onLogout: () => void;
}) {
  const { message } = AntApp.useApp();

  return (
    <div className="login-page account-password-page">
      <Card className="login-card account-password-card">
        <Space orientation="vertical" size={20} className="full">
          <div className="login-brand-lockup">
            <img src={sysuLogoSrc} alt="" />
            <div>
              <Text strong>中山大学</Text>
              <Text type="secondary" className="block-text">
                教师账户安全
              </Text>
            </div>
          </div>
          <div className="login-title">
            <Text className="eyebrow">首次登录</Text>
            <Title level={2}>请先设置你的新密码</Title>
            <Text type="secondary" className="block-text">
              {user.display_name || user.username}，完成改密后才能进入教师端。保存后系统会更新当前登录凭证，其他设备上的旧会话将失效。
            </Text>
          </div>
          <PasswordChangeForm
            submitLabel="修改密码并进入教师端"
            onChanged={(response) => {
              message.success("密码已修改");
              onChanged(response);
            }}
          />
          <Button type="text" icon={<LogoutOutlined />} block onClick={onLogout}>
            退出当前账号
          </Button>
        </Space>
      </Card>
    </div>
  );
}
