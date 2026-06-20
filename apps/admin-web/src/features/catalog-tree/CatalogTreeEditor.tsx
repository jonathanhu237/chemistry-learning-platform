import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Descriptions,
  Divider,
  Empty,
  Flex,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Radio,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
} from "antd";
import {
  CheckCircleOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  LinkOutlined,
  SaveOutlined,
  SearchOutlined,
  StopOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";

import type { CatalogNodeCard, CatalogNodeDetail } from "../../api/catalogTree";
import { getMediaAssetFileUrl, getMediaAssetThumbnailUrl } from "../../api/media";
import { QueryState } from "../../components/QueryState";
import { useCatalogMediaAssets, useCatalogSearch, useCatalogValidation, type useCatalogMutations } from "./catalogTreeHooks";
import {
  buildCatalogNodeUpdatePayload,
  buildCatalogPointContentPayload,
  buildCatalogRelatedLinksPayload,
  buildMovePayload,
  catalogNodeKindLabel,
  catalogStatusColor,
  hydrateCatalogNodeForm,
  hydrateCatalogPointContentForm,
  hydrateCatalogRelatedLinksForm,
  isPointCapable,
} from "./catalogTreeMappers";
import type { CatalogNodeFormValues, CatalogPointContentFormValues, CatalogRelatedLinksFormValues } from "./catalogTreeMappers";

const { Text, Title } = Typography;

type CatalogMutations = ReturnType<typeof useCatalogMutations>;

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2);
}

export function CatalogTreeEditor({
  detail,
  loading,
  error,
  siblings,
  onSelectNode,
  mutations,
}: {
  detail?: CatalogNodeDetail;
  loading?: boolean;
  error?: unknown;
  siblings: CatalogNodeCard[];
  onSelectNode: (nodeId: string) => void;
  mutations: CatalogMutations;
}) {
  const [nodeForm] = Form.useForm<CatalogNodeFormValues>();
  const [pointForm] = Form.useForm<CatalogPointContentFormValues>();
  const [linksForm] = Form.useForm<CatalogRelatedLinksFormValues>();
  const [moveParentId, setMoveParentId] = useState<string>("");
  const [moveDisplayOrder, setMoveDisplayOrder] = useState<number | null>(null);
  const [mediaAssetIds, setMediaAssetIds] = useState<string[]>([]);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [relatedQuery, setRelatedQuery] = useState("");
  const node = detail?.node;
  const pointCapable = isPointCapable(node?.node_kind);
  const principleMode = Form.useWatch("principle_mode", pointForm);
  const validation = useCatalogValidation(node?.node_id, true);
  const mediaAssets = useCatalogMediaAssets(pointCapable);
  const relatedSearch = useCatalogSearch(relatedQuery, node?.chapter_id, pointCapable);
  const mediaAssetMap = useMemo(
    () => new Map((mediaAssets.data?.items || []).map((asset) => [asset.id, asset])),
    [mediaAssets.data?.items],
  );
  const relatedTargetOptions = (relatedSearch.data?.items || [])
    .filter((item) => isPointCapable(item.node_kind) && item.node_id !== node?.node_id)
    .map((item) => ({ value: item.node_id, label: `${item.title} · ${catalogNodeKindLabel(item.node_kind)}` }));

  useEffect(() => {
    nodeForm.setFieldsValue(hydrateCatalogNodeForm(detail));
    pointForm.setFieldsValue(hydrateCatalogPointContentForm(detail));
    linksForm.setFieldsValue(hydrateCatalogRelatedLinksForm(detail));
    setMoveParentId(detail?.node.parent_id || "");
    setMoveDisplayOrder(detail?.node.display_order ?? null);
    setMediaAssetIds([]);
    setUploadTitle(detail?.node.title || "");
    setUploadFile(null);
  }, [detail, linksForm, nodeForm, pointForm]);

  if (!detail && !loading && !error) {
    return (
      <div className="catalog-editor-empty">
        <Empty description="请选择左侧目录节点" />
      </div>
    );
  }

  return (
    <QueryState loading={Boolean(loading)} error={error} empty={!detail}>
      {node ? (
        <div className="catalog-editor">
          <div className="catalog-editor-header">
            <Flex align="start" justify="space-between" gap={16}>
              <div>
                <Space size={8} wrap>
                  <Tag color={catalogStatusColor(node.status)}>{node.status}</Tag>
                  <Tag>{catalogNodeKindLabel(node.node_kind)}</Tag>
                  {node.has_children ? <Tag color="blue">子节点 {detail.children.length}</Tag> : null}
                  {pointCapable ? <Tag color="purple">视频 {node.published_media_count}/{node.media_count}</Tag> : null}
                </Space>
                <Title level={3}>{node.title}</Title>
                <Text type="secondary">{detail.breadcrumbs.map((item) => item.title).join(" / ")}</Text>
              </div>
              <Space wrap>
                {node.status === "archived" ? (
                  <Button onClick={() => mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action: "restore" })}>恢复</Button>
                ) : (
                  <Popconfirm title="归档该节点？" onConfirm={() => mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action: "archive" })}>
                    <Button danger icon={<DeleteOutlined />}>归档</Button>
                  </Popconfirm>
                )}
                {node.status === "published" ? (
                  <Button icon={<StopOutlined />} onClick={() => mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action: "unpublish" })}>
                    取消发布
                  </Button>
                ) : (
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    onClick={() => mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action: "publish", includeSubtree: false })}
                  >
                    发布节点
                  </Button>
                )}
              </Space>
            </Flex>
          </div>

          <section className="catalog-editor-section">
            <Flex align="center" justify="space-between">
              <Title level={4}>基础信息</Title>
              <Text type="secondary">Node ID: {node.node_id}</Text>
            </Flex>
            <Form form={nodeForm} layout="vertical" onFinish={(values) => mutations.updateNode.mutate({ nodeId: node.node_id, payload: buildCatalogNodeUpdatePayload(values) })}>
              <div className="catalog-form-grid">
                <Form.Item name="title" label="节点标题" rules={[{ required: true, message: "请输入节点标题" }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="node_kind" label="节点类型" rules={[{ required: true }]}>
                  <Radio.Group optionType="button" buttonStyle="solid">
                    <Radio.Button value="directory">目录</Radio.Button>
                    <Radio.Button value="point">点位</Radio.Button>
                    <Radio.Button value="hybrid">混合</Radio.Button>
                    <Radio.Button value="shortcut">快捷</Radio.Button>
                  </Radio.Group>
                </Form.Item>
              </div>
              <Form.Item name="summary" label="摘要">
                <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
              </Form.Item>
              <Form.Item noStyle shouldUpdate={(prev, next) => prev.node_kind !== next.node_kind}>
                {({ getFieldValue }) =>
                  getFieldValue("node_kind") === "shortcut" ? (
                    <Form.Item name="shortcut_target_node_id" label="快捷入口目标点位 Node ID" rules={[{ required: true, message: "请输入目标 Node ID" }]}>
                      <Input />
                    </Form.Item>
                  ) : null
                }
              </Form.Item>
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={mutations.updateNode.isPending}>
                保存基础信息
              </Button>
            </Form>
          </section>

          <section className="catalog-editor-section">
            <Title level={4}>位置与顺序</Title>
            <div className="catalog-form-grid">
              <Input value={moveParentId} onChange={(event) => setMoveParentId(event.target.value)} placeholder="父节点 ID，留空为章节根目录" />
              <InputNumber value={moveDisplayOrder ?? undefined} min={1} className="full" onChange={(value) => setMoveDisplayOrder(value ?? null)} placeholder="排序号" />
            </div>
            <Space wrap>
              <Button
                onClick={() => mutations.moveNode.mutate({ nodeId: node.node_id, payload: buildMovePayload(moveParentId, moveDisplayOrder) })}
                loading={mutations.moveNode.isPending}
              >
                移动节点
              </Button>
              <Text type="secondary">同级节点：{siblings.length}</Text>
            </Space>
          </section>

          {pointCapable ? (
            <>
              <section className="catalog-editor-section">
                <Flex align="center" justify="space-between" gap={12}>
                  <Title level={4}>点位内容</Title>
                  <Space wrap>
                    <Tag color={detail.point_content?.content_status === "published" ? "green" : "gold"}>
                      {detail.point_content?.content_status || "missing"}
                    </Tag>
                    <Button
                      icon={<CheckCircleOutlined />}
                      onClick={() => mutations.changePointPublication.mutate({ nodeId: node.node_id, action: "publish" })}
                      loading={mutations.changePointPublication.isPending}
                    >
                      发布点位
                    </Button>
                    <Button onClick={() => mutations.changePointPublication.mutate({ nodeId: node.node_id, action: "unpublish" })}>取消发布</Button>
                  </Space>
                </Flex>
                <Form
                  form={pointForm}
                  layout="vertical"
                  onFinish={(values) => mutations.savePointContent.mutate({ nodeId: node.node_id, payload: buildCatalogPointContentPayload(values) })}
                >
                  <Form.Item name="point_title" label="点位名" rules={[{ required: true, message: "请输入点位名" }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item name="teacher_note" label="老师备注">
                    <Input.TextArea className="catalog-teacher-note" autoSize={{ minRows: 2, maxRows: 5 }} placeholder="仅教师可见，不进入学生端、搜索、题目证据链" />
                  </Form.Item>
                  <Form.Item name="principle_mode" label="实验原理形式" rules={[{ required: true }]}>
                    <Radio.Group optionType="button" buttonStyle="solid">
                      <Radio.Button value="equation">化学方程式</Radio.Button>
                      <Radio.Button value="text">文字描述</Radio.Button>
                    </Radio.Group>
                  </Form.Item>
                  {principleMode === "equation" ? (
                    <Form.Item name="principle_equation" label="化学方程式" rules={[{ required: true, message: "请输入化学方程式" }]}>
                      <Input />
                    </Form.Item>
                  ) : (
                    <Form.Item name="principle_text" label="文字原理" rules={[{ required: true, message: "请输入文字原理" }]}>
                      <Input.TextArea autoSize={{ minRows: 3, maxRows: 7 }} />
                    </Form.Item>
                  )}
                  <Form.Item name="phenomenon_explanation" label="现象解释" rules={[{ required: true, message: "请输入现象解释" }]}>
                    <Input.TextArea autoSize={{ minRows: 3, maxRows: 7 }} />
                  </Form.Item>
                  <Form.Item name="safety_note" label="安全提示" rules={[{ required: true, message: "请输入安全提示" }]}>
                    <Input.TextArea autoSize={{ minRows: 2, maxRows: 5 }} />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={mutations.savePointContent.isPending}>
                    保存点位草稿
                  </Button>
                </Form>
              </section>

              <section className="catalog-editor-section">
                <Flex align="center" justify="space-between" gap={12}>
                  <Title level={4}>相关实验链接</Title>
                  <Input
                    prefix={<SearchOutlined />}
                    value={relatedQuery}
                    onChange={(event) => setRelatedQuery(event.target.value)}
                    placeholder="搜索可关联点位"
                    className="catalog-related-search"
                  />
                </Flex>
                <Form
                  form={linksForm}
                  layout="vertical"
                  onFinish={(values) => mutations.saveRelatedLinks.mutate({ nodeId: node.node_id, payload: buildCatalogRelatedLinksPayload(values) })}
                >
                  <Form.List name="links">
                    {(fields, { add, remove }) => (
                      <div className="catalog-related-list">
                        {fields.map((field) => (
                          <div className="catalog-related-row" key={field.key}>
                            <Form.Item name={[field.name, "target_node_id"]} rules={[{ required: true, message: "请选择目标点位" }]}>
                              <Select showSearch placeholder="目标点位 Node ID" options={relatedTargetOptions} loading={relatedSearch.isFetching} />
                            </Form.Item>
                            <Form.Item name={[field.name, "relation_type"]}>
                              <Select
                                options={[
                                  { value: "manual", label: "手动关联" },
                                  { value: "default_override", label: "默认覆盖" },
                                ]}
                              />
                            </Form.Item>
                            <Form.Item name={[field.name, "sort_order"]}>
                              <InputNumber min={1} className="full" />
                            </Form.Item>
                            <Form.Item name={[field.name, "label"]}>
                              <Input placeholder="显示名" />
                            </Form.Item>
                            <Button danger icon={<DeleteOutlined />} onClick={() => remove(field.name)} />
                          </div>
                        ))}
                        <Button icon={<LinkOutlined />} onClick={() => add({ relation_type: "manual", hidden: false, sort_order: fields.length + 1 })}>
                          添加链接
                        </Button>
                      </div>
                    )}
                  </Form.List>
                  <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={mutations.saveRelatedLinks.isPending}>
                    保存相关链接
                  </Button>
                </Form>
              </section>

              <section className="catalog-editor-section">
                <Title level={4}>视频绑定</Title>
                <div className="catalog-media-bind-toolbar">
                  <Select
                    mode="multiple"
                    allowClear
                    showSearch
                    value={mediaAssetIds}
                    onChange={setMediaAssetIds}
                    loading={mediaAssets.isFetching}
                    placeholder="选择后台视频素材"
                    options={(mediaAssets.data?.items || []).map((asset) => ({
                      value: asset.id,
                      label: `${asset.title || asset.original_file_name} · ${asset.upload_status}`,
                    }))}
                  />
                  <Button
                    icon={<VideoCameraOutlined />}
                    disabled={!mediaAssetIds.length}
                    loading={mutations.bindMedia.isPending}
                    onClick={() => mutations.bindMedia.mutate({ nodeId: node.node_id, assetIds: mediaAssetIds, assetMap: mediaAssetMap, status: "draft" })}
                  >
                    绑定素材
                  </Button>
                </div>
                <div className="catalog-upload-row">
                  <Input value={uploadTitle} onChange={(event) => setUploadTitle(event.target.value)} placeholder="上传标题" />
                  <input type="file" accept="video/*" onChange={(event) => setUploadFile(event.target.files?.[0] || null)} />
                  <Button
                    icon={<CloudUploadOutlined />}
                    disabled={!uploadFile}
                    loading={mutations.uploadMedia.isPending}
                    onClick={() => uploadFile && mutations.uploadMedia.mutate({ nodeId: node.node_id, title: uploadTitle || node.title, file: uploadFile })}
                  >
                    上传并绑定
                  </Button>
                </div>
                <div className="catalog-media-list">
                  {detail.media_bindings.length ? (
                    detail.media_bindings.map((binding) => (
                      <div className="catalog-media-row" key={binding.binding_id}>
                        <div className="catalog-media-thumb">
                          {binding.has_thumbnail ? <img src={getMediaAssetThumbnailUrl(binding.media_id)} alt="" /> : <VideoCameraOutlined />}
                        </div>
                        <div className="catalog-media-main">
                          <strong>{binding.title}</strong>
                          <Text type="secondary">{binding.original_file_name}</Text>
                          <Space size={6} wrap>
                            <Tag color={binding.binding_status === "published" ? "green" : "gold"}>{binding.binding_status}</Tag>
                            <Tag>{binding.upload_status}</Tag>
                            <a href={getMediaAssetFileUrl(binding.media_id)} target="_blank" rel="noreferrer">
                              <EyeOutlined /> 预览
                            </a>
                          </Space>
                        </div>
                        <Space wrap>
                          {binding.binding_status === "published" ? (
                            <Button onClick={() => mutations.changeMediaStatus.mutate({ bindingId: binding.binding_id, action: "unpublish" })}>取消发布</Button>
                          ) : (
                            <Button onClick={() => mutations.changeMediaStatus.mutate({ bindingId: binding.binding_id, action: "publish" })}>发布</Button>
                          )}
                          <Popconfirm title="删除该视频绑定？" onConfirm={() => mutations.changeMediaStatus.mutate({ bindingId: binding.binding_id, action: "delete" })}>
                            <Button danger icon={<DeleteOutlined />} />
                          </Popconfirm>
                        </Space>
                      </div>
                    ))
                  ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无绑定视频" />
                  )}
                </div>
              </section>
            </>
          ) : null}

          <section className="catalog-editor-section">
            <Flex align="center" justify="space-between">
              <Title level={4}>搜索预览与索引状态</Title>
              {detail.index_state ? <Tag color={detail.index_state.sync_status === "synced" ? "green" : "gold"}>{detail.index_state.sync_status}</Tag> : <Tag>未入队</Tag>}
            </Flex>
            {detail.search_preview ? (
              <pre className="catalog-search-preview">{prettyJson(detail.search_preview)}</pre>
            ) : (
              <Alert type="info" showIcon message="当前节点没有学生可见搜索文档" />
            )}
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="期望动作">{detail.index_state?.desired_action || "-"}</Descriptions.Item>
              <Descriptions.Item label="尝试次数">{detail.index_state?.attempts ?? "-"}</Descriptions.Item>
              <Descriptions.Item label="最近索引">{detail.index_state?.indexed_at || "-"}</Descriptions.Item>
              <Descriptions.Item label="错误">{detail.index_state?.last_error || "-"}</Descriptions.Item>
            </Descriptions>
          </section>

          <section className="catalog-editor-section">
            <Flex align="center" justify="space-between">
              <Title level={4}>发布验证</Title>
              {validation.isFetching ? <Spin size="small" /> : null}
            </Flex>
            {(validation.data || detail.validation)?.errors?.length ? (
              <Alert type="error" showIcon message="发布前需要修复" description={(validation.data || detail.validation).errors.join("；")} />
            ) : (
              <Alert type="success" showIcon message="当前节点可发布" />
            )}
            {(validation.data || detail.validation)?.warnings?.length ? (
              <>
                <Divider />
                <Alert type="warning" showIcon message="提示" description={(validation.data || detail.validation).warnings.join("；")} />
              </>
            ) : null}
          </section>
        </div>
      ) : null}
    </QueryState>
  );
}
