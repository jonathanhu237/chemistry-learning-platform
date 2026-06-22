import { useState } from "react";
import { App as AntApp, Button, Card, Form, Input, Space, Typography } from "antd";
import { useLocation, useNavigate } from "react-router-dom";

import type { LoginResponse } from "../../api/auth";
import { setAuthToken } from "../../api/auth";
import { api } from "../../api/http";
import { errorMessage } from "../../lib/errors";

const { Text, Title } = Typography;
const sysuLogoSrc = `${import.meta.env.BASE_URL}sysu-logo.svg`;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { message } = AntApp.useApp();
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const from = (location.state as { from?: string } | null)?.from || "/overview";

  const submit = async (values: { username: string; password: string }) => {
    setSubmitting(true);
    try {
      const response = await api<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(values),
      });
      if (response.user.role !== "admin" && response.user.role !== "teacher") {
        throw new Error("该账号不能登录教师后台");
      }
      setAuthToken(response.access_token);
      message.success("登录成功");
      navigate(from, { replace: true });
    } catch (error) {
      message.error(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <Card className="login-card">
        <Space orientation="vertical" size={20} className="full">
          <div className="login-brand-lockup">
            <img src={sysuLogoSrc} alt="" />
            <div>
              <Text strong>中山大学</Text>
              <Text type="secondary" className="block-text">
                SYSU Chemistry Learning
              </Text>
            </div>
          </div>
          <div className="login-title">
            <Text className="eyebrow">Teacher Console</Text>
            <Title level={2}>无机化学实验学习后台</Title>
            <Text type="secondary" className="block-text">
              管理实验点位、视频资源、题库与学生学习数据。
            </Text>
          </div>
          <Form form={form} layout="vertical" onFinish={submit} initialValues={{ username: "admin" }}>
            <Form.Item name="username" label="账号" rules={[{ required: true, message: "请输入账号" }]}>
              <Input size="large" autoComplete="username" />
            </Form.Item>
            <Form.Item name="password" label="密码" rules={[{ required: true, message: "请输入密码" }]}>
              <Input.Password size="large" autoComplete="current-password" />
            </Form.Item>
            <Button type="primary" size="large" htmlType="submit" loading={submitting} block>
              登录后台
            </Button>
          </Form>
        </Space>
      </Card>
    </div>
  );
}
