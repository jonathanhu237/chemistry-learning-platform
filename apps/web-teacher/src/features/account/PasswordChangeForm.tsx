import { useState } from "react";
import { App as AntApp, Button, Form, Input } from "antd";

import type { LoginResponse } from "../../api/auth";
import { changeOwnPassword } from "../../api/teacherAccounts";
import { errorMessage } from "../../lib/errors";

type PasswordValues = {
  current_password: string;
  new_password: string;
  confirm_password: string;
};

export function PasswordChangeForm({
  onChanged,
  submitLabel = "保存新密码",
}: {
  onChanged: (response: LoginResponse) => void;
  submitLabel?: string;
}) {
  const { message } = AntApp.useApp();
  const [form] = Form.useForm<PasswordValues>();
  const [submitting, setSubmitting] = useState(false);

  const submit = async (values: PasswordValues) => {
    setSubmitting(true);
    try {
      const response = await changeOwnPassword(values.current_password, values.new_password);
      form.resetFields();
      onChanged(response);
    } catch (error) {
      message.error(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Form<PasswordValues> form={form} layout="vertical" onFinish={submit} requiredMark={false}>
      <Form.Item name="current_password" label="当前密码" rules={[{ required: true, message: "请输入当前密码" }]}>
        <Input.Password autoComplete="current-password" />
      </Form.Item>
      <Form.Item
        name="new_password"
        label="新密码"
        rules={[
          { required: true, message: "请输入新密码" },
          { min: 8, message: "密码至少 8 位" },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || value !== getFieldValue("current_password")) return Promise.resolve();
              return Promise.reject(new Error("新密码不能与当前密码相同"));
            },
          }),
        ]}
      >
        <Input.Password autoComplete="new-password" />
      </Form.Item>
      <Form.Item
        name="confirm_password"
        label="确认新密码"
        dependencies={["new_password"]}
        rules={[
          { required: true, message: "请再次输入新密码" },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || value === getFieldValue("new_password")) return Promise.resolve();
              return Promise.reject(new Error("两次输入的新密码不一致"));
            },
          }),
        ]}
      >
        <Input.Password autoComplete="new-password" />
      </Form.Item>
      <Button type="primary" htmlType="submit" block loading={submitting}>
        {submitLabel}
      </Button>
    </Form>
  );
}
