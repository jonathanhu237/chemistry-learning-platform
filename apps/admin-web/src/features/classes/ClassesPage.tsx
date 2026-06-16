import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  App as AntApp,
  Button,
  Card,
  Drawer,
  Flex,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload,
} from "antd";
import {
  ArrowRightOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  EditOutlined,
  IdcardOutlined,
  KeyOutlined,
  PlusOutlined,
  SettingOutlined,
  TeamOutlined,
} from "@ant-design/icons";

import { api, patchJson, postJson, putJson } from "../../api";
import type { ClassItem, RegistrationSettings, RosterImportResult, RosterStudent } from "../../api";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { errorMessage } from "../../lib/errors";
import { statusTag } from "../../lib/status";
import "./classes.css";

const { Text, Title } = Typography;

export function ClassesPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [importingRoster, setImportingRoster] = useState(false);
  const [selectedClassId, setSelectedClassId] = useState<string>();
  const [rosterFile, setRosterFile] = useState<File | null>(null);
  const [importMode, setImportMode] = useState<"upsert" | "overwrite">("upsert");
  const [rosterView, setRosterView] = useState<"current" | "disabled">("current");
  const [studentSearch, setStudentSearch] = useState("");
  const [studentOpen, setStudentOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<RosterStudent | null>(null);
  const [classForm] = Form.useForm();
  const [classSettingsForm] = Form.useForm();
  const [registrationForm] = Form.useForm();
  const [studentForm] = Form.useForm();
  const classes = useQuery({ queryKey: ["classes"], queryFn: () => api<ClassItem[]>("/api/admin/classes") });
  const selectedClass = (classes.data || []).find((item) => item.id === selectedClassId) || null;
  const roster = useQuery({
    queryKey: ["class-roster", selectedClassId],
    queryFn: () => api<RosterStudent[]>(`/api/admin/classes/${selectedClassId}/students`),
    enabled: Boolean(selectedClassId),
  });
  const registration = useQuery({
    queryKey: ["class-registration-settings", selectedClassId],
    queryFn: () => api<RegistrationSettings>(`/api/admin/classes/${selectedClassId}/registration-settings`),
    enabled: Boolean(selectedClassId),
  });
  const defaultPasswordMode =
    Form.useWatch("default_password_mode", registrationForm) ||
    registration.data?.default_password_mode ||
    (registration.data?.has_default_password ? "shared" : "student_id");
  const classStatus = Form.useWatch("status", classSettingsForm) || selectedClass?.status || "active";
  const rosterRows = roster.data || [];
  const currentRoster = rosterRows.filter((row) => row.status !== "disabled");
  const disabledRoster = rosterRows.filter((row) => row.status === "disabled");
  const activeCount = currentRoster.filter((row) => row.activated || row.status === "active").length;
  const inactiveCount = currentRoster.length - activeCount;
  const tableRoster = rosterView === "current" ? currentRoster : disabledRoster;
  const normalizedStudentSearch = studentSearch.trim().toLowerCase();
  const filteredTableRoster = normalizedStudentSearch
    ? tableRoster.filter(
        (row) =>
          row.student_id.toLowerCase().includes(normalizedStudentSearch) ||
          row.student_name.toLowerCase().includes(normalizedStudentSearch),
      )
    : tableRoster;
  const initialPasswordLabel = defaultPasswordMode === "shared" ? "统一初始密码" : "使用学号";

  useEffect(() => {
    if (selectedClass) {
      classSettingsForm.setFieldsValue({
        class_name: selectedClass.class_name,
        description: selectedClass.description,
        status: selectedClass.status,
      });
    }
  }, [classSettingsForm, selectedClass]);

  useEffect(() => {
    if (registration.data) {
      registrationForm.setFieldsValue({
        ...registration.data,
        mode: "roster_only",
        default_password_mode:
          registration.data.default_password_mode || (registration.data.has_default_password ? "shared" : "student_id"),
        default_password: "",
      });
    }
  }, [registration.data, registrationForm]);

  useEffect(() => {
    if (!studentOpen) return;
    if (editingStudent) {
      studentForm.setFieldsValue(editingStudent);
    } else {
      studentForm.setFieldsValue({
        student_id: "",
        student_name: "",
      });
    }
  }, [editingStudent, studentForm, studentOpen]);

  const createClass = useMutation({
    mutationFn: (values: { class_name: string; description?: string }) => postJson<ClassItem>("/api/admin/classes", values),
    onSuccess: (item) => {
      message.success("班级已创建");
      setCreateOpen(false);
      classForm.resetFields();
      setSelectedClassId(item.id);
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateClass = useMutation({
    mutationFn: (values: { class_name?: string; description?: string; status?: string }) =>
      patchJson<ClassItem>(`/api/admin/classes/${selectedClassId}`, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateRegistration = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      const passwordMode = String(values.default_password_mode || "student_id");
      if (!selectedClassId) throw new Error("请先选择班级");
      return putJson<RegistrationSettings>(`/api/admin/classes/${selectedClassId}/registration-settings`, {
        mode: "roster_only",
        default_password_policy: "student_id_name_activation",
        default_password_mode: passwordMode,
        default_password: passwordMode === "shared" ? values.default_password || undefined : undefined,
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["class-registration-settings", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const saveStudent = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      if (editingStudent) {
        return patchJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${editingStudent.student_id}`, values);
      }
      return postJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students`, values);
    },
    onSuccess: () => {
      message.success(editingStudent ? "学生已更新" : "学生已添加");
      setStudentOpen(false);
      setEditingStudent(null);
      studentForm.resetFields();
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const disableStudent = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return api<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${studentId}`, { method: "DELETE" });
    },
    onSuccess: () => {
      message.success("学生已禁用");
      setRosterView("current");
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const resetPassword = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return postJson(`/api/admin/classes/${selectedClassId}/students/${studentId}/reset-password`, { force_change: true });
    },
    onSuccess: () => message.success("已重置为学号初始密码"),
    onError: (error) => message.error(errorMessage(error)),
  });

  const restoreStudent = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return patchJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${studentId}`, { status: "pending" });
    },
    onSuccess: () => {
      message.success("学生已恢复到当前名单");
      setRosterView("current");
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const saveClassConfiguration = async () => {
    try {
      const [classValues, registrationValues] = await Promise.all([
        classSettingsForm.validateFields(),
        registrationForm.validateFields(),
      ]);
      await updateClass.mutateAsync(classValues);
      await updateRegistration.mutateAsync(registrationValues);
      message.success("班级设置已保存");
      setSettingsOpen(false);
    } catch (error) {
      if (error instanceof Error) {
        message.error(errorMessage(error));
      }
    }
  };

  const importRoster = async () => {
    if (!selectedClassId || !rosterFile) {
      message.warning("请先选择名单文件");
      return;
    }
    const body = new FormData();
    body.append("file", rosterFile);
    body.append("mode", importMode);
    setImportingRoster(true);
    try {
      const result = await api<RosterImportResult>(`/api/admin/classes/${selectedClassId}/roster/import`, { method: "POST", body });
      message.success(
        importMode === "overwrite"
          ? `覆盖导入完成：${result.valid_rows} 条有效，禁用 ${result.disabled_missing} 条缺失名单`
          : `导入完成：${result.valid_rows} 条有效`,
      );
      setRosterFile(null);
      setImportOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    } catch (error) {
      message.error(errorMessage(error));
    } finally {
      setImportingRoster(false);
    }
  };

  const openStudentEditor = (student?: RosterStudent) => {
    setEditingStudent(student || null);
    setStudentOpen(true);
  };

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="班级与学生" description="一个班级一张卡片；多个班级可以同时使用，点击卡片后管理班级名单。" />
      <QueryState loading={classes.isLoading} error={classes.error}>
        <div className="class-card-grid">
          {(classes.data || []).map((item) => (
            <Card
              key={item.id}
              hoverable
              className="class-card"
              onClick={() => setSelectedClassId(item.id)}
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter") setSelectedClassId(item.id);
              }}
            >
              <div className="class-card-content">
                <Flex justify="space-between" align="flex-start" gap={12}>
                  <div>
                    <Text className="eyebrow">班级</Text>
                    <Title level={4} className="class-card-title">{item.class_name}</Title>
                  </div>
                  {statusTag(item.status)}
                </Flex>
                <Text type="secondary" className="class-card-description">
                  {item.description || "暂无班级说明"}
                </Text>
                <Flex justify="space-between" align="end" className="class-card-footer">
                  <Statistic title="当前名单" value={item.student_count || 0} prefix={<TeamOutlined />} />
                  <Text className="class-card-action">
                    <ArrowRightOutlined /> 进入管理
                  </Text>
                </Flex>
              </div>
            </Card>
          ))}
          <button type="button" className="class-create-card" onClick={() => setCreateOpen(true)}>
            <PlusOutlined />
            <Text strong>新建班级</Text>
            <Text type="secondary">填写班级名称后即可导入名单</Text>
          </button>
        </div>
      </QueryState>

      <Drawer
        title={selectedClass ? selectedClass.class_name : "班级详情"}
        open={Boolean(selectedClassId)}
        onClose={() => {
          setSelectedClassId(undefined);
          setRosterFile(null);
          setStudentSearch("");
          setSettingsOpen(false);
          setImportOpen(false);
        }}
        width={980}
      >
        {selectedClass ? (
          <Space direction="vertical" size={18} className="full">
            <div className="class-detail-hero">
              <div className="class-detail-copy">
                <Text className="eyebrow">班级管理</Text>
                <Title level={3}>{selectedClass.class_name}</Title>
                <Space wrap className="class-hero-meta">
                  {statusTag(selectedClass.status)}
                  <Tag color="blue">初始密码：{initialPasswordLabel}</Tag>
                </Space>
                <Text type="secondary" className="class-detail-description">
                  {selectedClass.description || "暂无班级说明"}
                </Text>
              </div>
              <div className="class-hero-side">
                <div className="class-hero-actions">
                  <Button type="primary" icon={<SettingOutlined />} onClick={() => setSettingsOpen(true)}>
                    编辑班级设置
                  </Button>
                </div>
                <div className="class-hero-stats">
                  <Statistic title="当前名单" value={currentRoster.length} prefix={<IdcardOutlined />} />
                  <Statistic title="已激活" value={activeCount} />
                  <Statistic title="未激活" value={inactiveCount} />
                  <Statistic title="已禁用" value={disabledRoster.length} />
                </div>
              </div>
            </div>

            <div className="drawer-section roster-section">
              <Flex justify="space-between" align="flex-start" gap={16} className="drawer-table-heading roster-heading">
                <div className="roster-heading-copy">
                  <Text strong>学生名单</Text>
                  <Text type="secondary" className="block-text">
                    导入或添加即完成班级登记；学生首次登录并修改密码后才算已激活。
                  </Text>
                </div>
                <Space className="roster-heading-actions" size={10}>
                  <Button icon={<CloudUploadOutlined />} onClick={() => setImportOpen(true)}>
                    导入名单
                  </Button>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => openStudentEditor()}>
                    添加学生
                  </Button>
                </Space>
              </Flex>
              <Tabs
                activeKey={rosterView}
                onChange={(key) => setRosterView(key as "current" | "disabled")}
                tabBarExtraContent={
                  <Input.Search
                    allowClear
                    className="roster-search"
                    placeholder="搜索学号或姓名"
                    value={studentSearch}
                    onChange={(event) => setStudentSearch(event.target.value)}
                  />
                }
                items={[
                  { key: "current", label: `当前名单 (${currentRoster.length})` },
                  { key: "disabled", label: `已禁用 (${disabledRoster.length})` },
                ]}
              />
              <QueryState loading={roster.isLoading} error={roster.error} empty={!filteredTableRoster.length}>
                <Table<RosterStudent>
                  rowKey="id"
                  dataSource={filteredTableRoster}
                  pagination={{ pageSize: 10, showSizeChanger: true }}
                  size="middle"
                  columns={[
                    { title: "学号", dataIndex: "student_id", width: 150 },
                    { title: "姓名", dataIndex: "student_name" },
                    {
                      title: "状态",
                      width: 120,
                      render: (_: unknown, row) => {
                        if (row.status === "disabled") return <Tag>已禁用</Tag>;
                        if (row.activated || row.status === "active") return <Tag color="green">已激活</Tag>;
                        return <Tag color="gold">未激活</Tag>;
                      },
                    },
                    {
                      title: "操作",
                      width: rosterView === "current" ? 250 : 150,
                      render: (_: unknown, row) => (
                        <Space>
                          <Button icon={<EditOutlined />} onClick={() => openStudentEditor(row)}>
                            编辑
                          </Button>
                          {rosterView === "current" ? (
                            <>
                              <Button icon={<KeyOutlined />} disabled={!row.activated} onClick={() => resetPassword.mutate(row.student_id)}>
                                重置
                              </Button>
                              <Popconfirm title="确认禁用该学生？" onConfirm={() => disableStudent.mutate(row.student_id)}>
                                <Button danger icon={<DeleteOutlined />}>
                                  禁用
                                </Button>
                              </Popconfirm>
                            </>
                          ) : (
                            <Button onClick={() => restoreStudent.mutate(row.student_id)}>
                              恢复
                            </Button>
                          )}
                        </Space>
                      ),
                    },
                  ]}
                />
              </QueryState>
            </div>

          </Space>
        ) : null}
      </Drawer>

      <Modal
        title="班级设置"
        open={settingsOpen}
        okText="保存设置"
        cancelText="取消"
        width={720}
        confirmLoading={updateClass.isPending || updateRegistration.isPending}
        onCancel={() => setSettingsOpen(false)}
        onOk={() => void saveClassConfiguration()}
      >
        <QueryState loading={registration.isLoading} error={registration.error}>
          <Space direction="vertical" size={18} className="full">
            <div className="modal-section">
              <Text strong>班级基本信息</Text>
              <Text type="secondary" className="block-text">
                用于老师后台识别班级，学生端只感知自己所属班级。
              </Text>
              <Form form={classSettingsForm} layout="vertical" className="modal-form">
                <Form.Item name="class_name" label="班级名称" rules={[{ required: true, message: "请输入班级名称" }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="description" label="班级说明" rules={[{ max: 200, message: "班级说明请控制在 200 字以内" }]}>
                  <Input.TextArea rows={3} maxLength={200} showCount className="fixed-textarea" />
                </Form.Item>
                <Form.Item name="status" hidden>
                  <Input />
                </Form.Item>
                <div className="option-group-label">班级状态</div>
                <div className="choice-grid two compact">
                  <button
                    type="button"
                    className={`choice-card ${classStatus === "active" ? "choice-card-active" : ""}`}
                    onClick={() => classSettingsForm.setFieldsValue({ status: "active" })}
                  >
                    <Text strong>使用中</Text>
                    <Text type="secondary">学生可以继续学习和做题。</Text>
                  </button>
                  <button
                    type="button"
                    className={`choice-card ${classStatus === "archived" ? "choice-card-active" : ""}`}
                    onClick={() => classSettingsForm.setFieldsValue({ status: "archived" })}
                  >
                    <Text strong>已归档</Text>
                    <Text type="secondary">保留记录，不再作为当前运营班级。</Text>
                  </button>
                </div>
              </Form>
            </div>

            <div className="modal-section">
              <Text strong>登录规则</Text>
              <Text type="secondary" className="block-text">
                当前名单内学生首次登录时使用这里设置的初始密码；完成改密后才算已激活。
              </Text>
              <Form form={registrationForm} layout="vertical" className="modal-form">
                <Form.Item name="mode" hidden>
                  <Input />
                </Form.Item>
                <Form.Item name="default_password_mode" hidden>
                  <Input />
                </Form.Item>
                <div className="option-group-label">初始密码</div>
                <div className="choice-grid two">
                  <button
                    type="button"
                    className={`choice-card ${defaultPasswordMode === "student_id" ? "choice-card-active" : ""}`}
                    onClick={() => registrationForm.setFieldsValue({ default_password_mode: "student_id", default_password: "" })}
                  >
                    <Text strong>使用学号</Text>
                    <Text type="secondary">初始密码等于学号，适合演示和小班。</Text>
                  </button>
                  <button
                    type="button"
                    className={`choice-card ${defaultPasswordMode === "shared" ? "choice-card-active" : ""}`}
                    onClick={() => registrationForm.setFieldsValue({ default_password_mode: "shared" })}
                  >
                    <Text strong>统一初始密码</Text>
                    <Text type="secondary">老师设置一个统一密码，学生首次登录后修改。</Text>
                  </button>
                </div>
                {defaultPasswordMode === "shared" ? (
                  <Form.Item
                    name="default_password"
                    label="统一初始密码"
                    extra={registration.data?.has_default_password ? "留空则继续使用当前统一密码。" : "至少 8 位。"}
                    rules={[
                      {
                        validator: (_, value) => {
                          if (!value && registration.data?.has_default_password) return Promise.resolve();
                          if (!value) return Promise.reject(new Error("请输入统一初始密码"));
                          if (String(value).length < 8) return Promise.reject(new Error("至少 8 位"));
                          return Promise.resolve();
                        },
                      },
                    ]}
                  >
                    <Input.Password placeholder="输入新的统一初始密码" />
                  </Form.Item>
                ) : (
                  <Form.Item label="当前初始密码" extra="初始密码等于学生学号，学生首次登录后必须修改。">
                    <Input value="使用学生学号" disabled />
                  </Form.Item>
                )}
              </Form>
            </div>
          </Space>
        </QueryState>
      </Modal>

      <Modal
        title="导入学生名单"
        open={importOpen}
        okText="导入名单"
        cancelText="取消"
        width={640}
        confirmLoading={importingRoster}
        okButtonProps={{ disabled: !rosterFile }}
        onCancel={() => {
          setImportOpen(false);
          setRosterFile(null);
        }}
        onOk={() => void importRoster()}
      >
        <Space direction="vertical" size={16} className="full">
          <Text type="secondary">上传 CSV/XLSX。普通导入适合补充名单，覆盖导入适合用一份新名单替换当前名单。</Text>
          <div className="choice-grid two">
            <button
              type="button"
              className={`choice-card ${importMode === "upsert" ? "choice-card-active" : ""}`}
              onClick={() => setImportMode("upsert")}
            >
              <Text strong>普通导入</Text>
              <Text type="secondary">新增学生，更新已有学生姓名，不影响缺失学生。</Text>
            </button>
            <button
              type="button"
              className={`choice-card ${importMode === "overwrite" ? "choice-card-active" : ""}`}
              onClick={() => setImportMode("overwrite")}
            >
              <Text strong>覆盖导入</Text>
              <Text type="secondary">以本次文件为准，缺失学生会被禁用。</Text>
            </button>
          </div>
          <Upload
            maxCount={1}
            beforeUpload={(file) => {
              setRosterFile(file as File);
              return false;
            }}
            onRemove={() => setRosterFile(null)}
          >
            <Button icon={<CloudUploadOutlined />}>选择 CSV/XLSX</Button>
          </Upload>
        </Space>
      </Modal>

      <Modal
        title="新建班级"
        open={createOpen}
        okText="创建班级"
        cancelText="取消"
        confirmLoading={createClass.isPending}
        onCancel={() => setCreateOpen(false)}
        onOk={() => classForm.submit()}
      >
        <Text type="secondary" className="modal-helper">
          只需要填写班级名称，后续可以在班级卡片里导入学生名单。
        </Text>
        <Form form={classForm} layout="vertical" onFinish={(values) => createClass.mutate(values)}>
          <Form.Item name="class_name" label="班级名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="班级说明" rules={[{ max: 200, message: "班级说明请控制在 200 字以内" }]}>
            <Input.TextArea rows={3} maxLength={200} showCount className="fixed-textarea" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingStudent ? "编辑学生" : "添加学生"}
        open={studentOpen}
        okText={editingStudent ? "保存学生" : "添加学生"}
        cancelText="取消"
        onCancel={() => {
          setStudentOpen(false);
          setEditingStudent(null);
        }}
        onOk={() => studentForm.submit()}
      >
        <Text type="secondary" className="modal-helper">
          添加或导入即完成班级登记；学生首次登录并修改密码后会显示为已激活。
        </Text>
        <Form form={studentForm} layout="vertical" onFinish={(values) => saveStudent.mutate(values)}>
          <Form.Item name="student_id" label="学号" rules={[{ required: true }]}>
            <Input disabled={Boolean(editingStudent?.activated)} />
          </Form.Item>
          <Form.Item name="student_name" label="姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
