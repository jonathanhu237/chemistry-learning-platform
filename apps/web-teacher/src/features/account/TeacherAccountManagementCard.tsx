import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  App as AntApp,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import { KeyOutlined, PlusOutlined, StopOutlined, UnlockOutlined } from "@ant-design/icons";

import type { User } from "../../api/auth";
import {
  createTeacherAccount,
  disableTeacherAccount,
  enableTeacherAccount,
  listTeacherAccounts,
  resetTeacherAccountPassword,
  type TeacherAccount,
  type TeacherAccountCreate,
} from "../../api/teacherAccounts";
import { errorMessage } from "../../lib/errors";
import "./account.css";

const { Text } = Typography;

type CreateValues = TeacherAccountCreate & { confirm_password: string };
type ResetValues = { password: string; confirm_password: string };

function accountRoleLabel(role: TeacherAccount["role"]) {
  return role === "admin" ? "主管教师" : "教师";
}

export function TeacherAccountManagementCard({ currentUser }: { currentUser: User }) {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [resetTarget, setResetTarget] = useState<TeacherAccount | null>(null);
  const [createForm] = Form.useForm<CreateValues>();
  const [resetForm] = Form.useForm<ResetValues>();
  const accounts = useQuery({
    queryKey: ["teacher-accounts"],
    queryFn: listTeacherAccounts,
    enabled: currentUser.role === "admin",
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["teacher-accounts"] });
  const createMutation = useMutation({
    mutationFn: createTeacherAccount,
    onSuccess: () => {
      message.success("教师账号已创建");
      setCreateOpen(false);
      createForm.resetFields();
      void refresh();
    },
    onError: (error) => message.error(errorMessage(error)),
  });
  const resetMutation = useMutation({
    mutationFn: ({ id, password }: { id: string; password: string }) => resetTeacherAccountPassword(id, password),
    onSuccess: () => {
      message.success("密码已重置，该教师需要在下次登录时修改密码");
      setResetTarget(null);
      resetForm.resetFields();
      void refresh();
    },
    onError: (error) => message.error(errorMessage(error)),
  });
  const statusMutation = useMutation({
    mutationFn: ({ account, enable }: { account: TeacherAccount; enable: boolean }) =>
      enable ? enableTeacherAccount(account.id) : disableTeacherAccount(account.id),
    onSuccess: (account) => {
      message.success(`${account.display_name || account.username}已${account.status === "active" ? "启用" : "停用"}`);
      void refresh();
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  if (currentUser.role !== "admin") return null;

  return (
    <Card
      className="teacher-account-card"
      title="教师账号"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          新建教师账号
        </Button>
      }
    >
      <Text type="secondary">
        主管教师可以创建、重置、停用或启用教师账号。新账号和被重置的账号首次登录都必须修改密码；账号不会被删除，以保留历史内容归属。
      </Text>
      <Table<TeacherAccount>
        rowKey="id"
        size="middle"
        loading={accounts.isLoading}
        dataSource={accounts.data || []}
        pagination={false}
        locale={{ emptyText: accounts.isError ? errorMessage(accounts.error) : "暂无教师账号" }}
        columns={[
          {
            title: "教师",
            key: "identity",
            render: (_, account) => (
              <div className="teacher-account-identity">
                <Space size={6}>
                  <Text strong>{account.display_name || account.username}</Text>
                  {account.id === currentUser.id ? <Tag color="blue">本人</Tag> : null}
                </Space>
                <Text type="secondary">{account.username}</Text>
              </div>
            ),
          },
          {
            title: "权限",
            dataIndex: "role",
            width: 120,
            render: (role: TeacherAccount["role"]) => <Tag color={role === "admin" ? "green" : "default"}>{accountRoleLabel(role)}</Tag>,
          },
          {
            title: "状态",
            key: "status",
            width: 180,
            render: (_, account) => (
              <Space size={6} wrap>
                <Tag color={account.status === "active" ? "success" : "default"}>
                  {account.status === "active" ? "已启用" : "已停用"}
                </Tag>
                {account.must_change_password ? <Tag color="gold">待修改密码</Tag> : null}
              </Space>
            ),
          },
          {
            title: "操作",
            key: "actions",
            width: 250,
            align: "right",
            render: (_, account) =>
              account.id === currentUser.id ? (
                <Text type="secondary">请从右上角修改自己的密码</Text>
              ) : (
                <Space>
                  <Button icon={<KeyOutlined />} onClick={() => setResetTarget(account)}>
                    重置密码
                  </Button>
                  {account.status === "active" ? (
                    <Popconfirm
                      title={`停用 ${account.display_name || account.username}？`}
                      description="停用后该账号的现有会话会立即失效。"
                      okText="停用"
                      cancelText="取消"
                      onConfirm={() => statusMutation.mutate({ account, enable: false })}
                    >
                      <Button danger icon={<StopOutlined />} loading={statusMutation.isPending}>
                        停用
                      </Button>
                    </Popconfirm>
                  ) : (
                    <Button
                      icon={<UnlockOutlined />}
                      loading={statusMutation.isPending}
                      onClick={() => statusMutation.mutate({ account, enable: true })}
                    >
                      启用
                    </Button>
                  )}
                </Space>
              ),
          },
        ]}
      />

      <Modal
        title="新建教师账号"
        open={createOpen}
        okText="创建账号"
        cancelText="取消"
        confirmLoading={createMutation.isPending}
        onOk={() => createForm.submit()}
        onCancel={() => setCreateOpen(false)}
        destroyOnHidden
      >
        <Form<CreateValues>
          form={createForm}
          layout="vertical"
          requiredMark={false}
          onFinish={({ confirm_password: _confirm, ...values }) => createMutation.mutate(values)}
        >
          <Form.Item name="username" label="登录账号" rules={[{ required: true, message: "请输入登录账号" }]}>
            <Input autoComplete="off" />
          </Form.Item>
          <Form.Item name="display_name" label="教师姓名" rules={[{ required: true, message: "请输入教师姓名" }]}>
            <Input autoComplete="name" />
          </Form.Item>
          <Form.Item name="password" label="初始密码" rules={[{ required: true, min: 8, message: "密码至少 8 位" }]}>
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认初始密码"
            dependencies={["password"]}
            rules={[
              { required: true, message: "请再次输入初始密码" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || value === getFieldValue("password")) return Promise.resolve();
                  return Promise.reject(new Error("两次输入的密码不一致"));
                },
              }),
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`重置密码${resetTarget ? ` · ${resetTarget.display_name || resetTarget.username}` : ""}`}
        open={Boolean(resetTarget)}
        okText="重置密码"
        cancelText="取消"
        confirmLoading={resetMutation.isPending}
        onOk={() => resetForm.submit()}
        onCancel={() => setResetTarget(null)}
        destroyOnHidden
      >
        <Text type="secondary" className="account-modal-description">
          保存后该账号的现有会话立即失效，下次登录必须修改密码。
        </Text>
        <Form<ResetValues>
          form={resetForm}
          layout="vertical"
          requiredMark={false}
          onFinish={(values) => {
            if (resetTarget) resetMutation.mutate({ id: resetTarget.id, password: values.password });
          }}
        >
          <Form.Item name="password" label="新初始密码" rules={[{ required: true, min: 8, message: "密码至少 8 位" }]}>
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认新初始密码"
            dependencies={["password"]}
            rules={[
              { required: true, message: "请再次输入新初始密码" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || value === getFieldValue("password")) return Promise.resolve();
                  return Promise.reject(new Error("两次输入的密码不一致"));
                },
              }),
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
