import { Button, Empty, Popconfirm, Select, Space, Tag, Typography } from "antd";
import { ArrowRightOutlined, DeleteOutlined, EyeOutlined, VideoCameraOutlined } from "@ant-design/icons";
import type { UseQueryResult } from "@tanstack/react-query";

import type { ApiList } from "../../api/common";
import type { CatalogNodeDetail } from "../../api/catalogTree";
import { getMediaAssetFileUrl, getMediaAssetThumbnailUrl, type MediaAsset } from "../../api/media";
import type { CatalogMutations } from "./catalogTreeHooks";
import { isPointCapable } from "./catalogTreeMappers";

const { Text, Title } = Typography;

export function CatalogVideoPanel({
  detail,
  mediaAssets,
  mediaAssetIds,
  setMediaAssetIds,
  mediaAssetMap,
  mutations,
}: {
  detail: CatalogNodeDetail;
  mediaAssets: UseQueryResult<ApiList<MediaAsset>>;
  mediaAssetIds: string[];
  setMediaAssetIds: (ids: string[]) => void;
  mediaAssetMap: Map<string, MediaAsset>;
  mutations: CatalogMutations;
}) {
  const { node } = detail;

  if (!isPointCapable(node.node_kind)) {
    return (
      <section className="catalog-editor-section catalog-editor-panel-section">
        <Title level={4}>视频绑定</Title>
        <Text type="secondary">目录节点不绑定视频。请选择点位节点维护视频素材。</Text>
      </section>
    );
  }

  return (
    <section className="catalog-editor-section catalog-editor-panel-section">
      <div className="catalog-video-panel-heading">
        <div>
          <Title level={4}>视频绑定</Title>
          <Text type="secondary">这里只绑定已有素材；新视频请先到视频资源页上传。</Text>
        </div>
        <a className="catalog-video-shortcut-card" href="/videos">
          <span className="catalog-video-shortcut-icon">
            <VideoCameraOutlined />
          </span>
          <span>
            <strong>视频资源入口</strong>
            <small>上传后回到这里绑定</small>
          </span>
          <ArrowRightOutlined />
        </a>
      </div>
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
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂未绑定视频" />
        )}
      </div>
    </section>
  );
}
