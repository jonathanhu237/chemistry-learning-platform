import { useMemo, useState } from "react";
import { Button, Empty, Input, Modal, Popconfirm, Tag, Typography } from "antd";
import {
  ArrowRightOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlayCircleFilled,
  SearchOutlined,
  SwapOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";
import type { UseQueryResult } from "@tanstack/react-query";

import type { ApiList } from "../../api/common";
import type { CatalogMediaBinding, CatalogNodeDetail } from "../../api/catalogTree";
import { getMediaAssetFileUrl, getMediaAssetThumbnailUrl, type MediaAsset } from "../../api/media";
import type { CatalogMutations } from "./catalogTreeHooks";
import { isPointCapable } from "./catalogTreeMappers";

const { Text, Title } = Typography;

function isReadyVideo(asset: Pick<MediaAsset, "upload_status">): boolean {
  return asset.upload_status === "ready";
}

function isVideoAsset(asset: MediaAsset): boolean {
  const mime = `${asset.playback_mime_type || ""} ${asset.mime_type || ""}`.toLowerCase();
  return mime.includes("video") || /\.(mp4|m4v|mov|webm|avi|mkv)$/i.test(asset.original_file_name || "");
}

function assetTitle(asset: MediaAsset): string {
  return asset.title || asset.original_file_name || "未命名视频";
}

function readinessLabel(status: string): string {
  if (status === "ready") return "可播放";
  if (status === "failed") return "处理失败";
  if (status === "processing") return "处理中";
  if (status === "uploaded") return "待处理";
  return status || "未知状态";
}

function readinessColor(status: string): "green" | "orange" | "red" | "default" {
  if (status === "ready") return "green";
  if (status === "failed") return "red";
  if (status === "processing" || status === "uploaded") return "orange";
  return "default";
}

function formatDuration(seconds?: number | null): string | null {
  if (!seconds || seconds <= 0) return null;
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

function VideoThumbnail({
  assetId,
  hasThumbnail,
}: {
  assetId: string;
  hasThumbnail?: boolean;
}) {
  return (
    <div className="catalog-video-thumb">
      {hasThumbnail ? <img src={getMediaAssetThumbnailUrl(assetId)} alt="" /> : <VideoCameraOutlined />}
    </div>
  );
}

function CurrentVideoSlot({
  binding,
  canBindVideo,
  onOpenPicker,
  onRemove,
  removing,
}: {
  binding?: CatalogMediaBinding | null;
  canBindVideo: boolean;
  onOpenPicker: () => void;
  onRemove: () => void;
  removing: boolean;
}) {
  const [previewOpen, setPreviewOpen] = useState(false);

  if (!binding) {
    return (
      <button
        type="button"
        className="catalog-video-empty-slot"
        disabled={!canBindVideo}
        onClick={onOpenPicker}
      >
        <span className="catalog-video-empty-icon" aria-hidden="true">
          <VideoCameraOutlined />
        </span>
        <span className="catalog-video-empty-copy">
          <strong>选择视频素材</strong>
          <small>{canBindVideo ? "从视频资源中选择一个已就绪视频，选择后自动绑定" : "请先补全点位内容后再绑定视频"}</small>
        </span>
      </button>
    );
  }

  const mediaUrl = getMediaAssetFileUrl(binding.media_id);
  const posterUrl = binding.has_thumbnail ? getMediaAssetThumbnailUrl(binding.media_id) : undefined;

  return (
    <>
      <div className="catalog-video-current">
        <button
          type="button"
          className="catalog-video-play-card"
          onClick={() => setPreviewOpen(true)}
          aria-label={`播放视频：${binding.title}`}
        >
          <VideoThumbnail assetId={binding.media_id} hasThumbnail={binding.has_thumbnail} />
          <span className="catalog-video-play-overlay" aria-hidden="true">
            <PlayCircleFilled />
          </span>
        </button>
        <div className="catalog-video-current-side">
          <div className="catalog-video-current-main">
            <strong title={binding.title}>{binding.title}</strong>
            <Text type="secondary" title={binding.original_file_name}>
              {binding.original_file_name}
            </Text>
          </div>
          <div className="catalog-video-current-actions">
            <Button icon={<SwapOutlined />} onClick={onOpenPicker} disabled={!canBindVideo}>
              更换
            </Button>
            <Popconfirm title="删除当前视频绑定？" onConfirm={onRemove}>
              <Button danger icon={<DeleteOutlined />} loading={removing}>
                删除
              </Button>
            </Popconfirm>
          </div>
        </div>
      </div>
      <Modal
        className="catalog-video-preview-modal"
        title={binding.title}
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={null}
        width={920}
        destroyOnHidden
      >
        <video controls autoPlay preload="metadata" className="catalog-video-preview-player" src={mediaUrl} poster={posterUrl} />
      </Modal>
    </>
  );
}

function CatalogVideoPicker({
  open,
  currentMediaId,
  mediaAssets,
  pendingMediaId,
  onCancel,
  onSelect,
}: {
  open: boolean;
  currentMediaId?: string | null;
  mediaAssets: UseQueryResult<ApiList<MediaAsset>>;
  pendingMediaId?: string | null;
  onCancel: () => void;
  onSelect: (asset: MediaAsset) => void;
}) {
  const [query, setQuery] = useState("");
  const bindingInProgress = Boolean(pendingMediaId);
  const assets = useMemo(
    () =>
      (mediaAssets.data?.items || [])
        .filter(isVideoAsset)
        .filter((asset) => {
          const text = `${assetTitle(asset)} ${asset.original_file_name || ""}`.toLowerCase();
          return !query.trim() || text.includes(query.trim().toLowerCase());
        }),
    [mediaAssets.data?.items, query],
  );

  return (
    <Modal
      className="catalog-video-picker-modal"
      title="选择视频素材"
      open={open}
      onCancel={onCancel}
      footer={null}
      width={860}
      destroyOnHidden
    >
      <Input
        className="catalog-video-picker-search"
        allowClear
        prefix={<SearchOutlined />}
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="搜索视频标题或文件名"
      />
      <div className="catalog-video-picker-list">
        {assets.length ? (
          assets.map((asset) => {
            const ready = isReadyVideo(asset);
            const current = currentMediaId === asset.id;
            const selecting = pendingMediaId === asset.id;
            return (
              <div className={`catalog-video-picker-row ${!ready ? "is-disabled" : ""}`} key={asset.id}>
                <VideoThumbnail assetId={asset.id} hasThumbnail={Boolean(asset.thumbnail_relative_path)} />
                <div className="catalog-video-picker-main">
                  <strong title={assetTitle(asset)}>{assetTitle(asset)}</strong>
                  <Text type="secondary" title={asset.original_file_name}>
                    {asset.original_file_name}
                  </Text>
                  <div className="catalog-video-picker-meta">
                    <Tag color={readinessColor(asset.upload_status)}>{readinessLabel(asset.upload_status)}</Tag>
                    {asset.processing_phase ? <Tag>{asset.processing_phase}</Tag> : null}
                    {formatDuration(asset.duration_seconds) ? <Tag>{formatDuration(asset.duration_seconds)}</Tag> : null}
                  </div>
                  {asset.error_reason ? <Text type="danger">{asset.error_reason}</Text> : null}
                </div>
                <div className="catalog-video-picker-actions">
                  <Button type="link" href={getMediaAssetFileUrl(asset.id)} target="_blank" rel="noreferrer" icon={<EyeOutlined />}>
                    预览
                  </Button>
                  <Button
                    type="primary"
                    disabled={!ready || current || (bindingInProgress && !selecting)}
                    loading={selecting}
                    onClick={() => onSelect(asset)}
                  >
                    {current ? "当前视频" : selecting ? "选择中" : ready ? "选择" : "未就绪"}
                  </Button>
                </div>
              </div>
            );
          })
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={mediaAssets.isFetching ? "正在加载视频素材" : "没有匹配的视频素材"} />
        )}
      </div>
    </Modal>
  );
}

export function CatalogVideoPanel({
  detail,
  mediaAssets,
  mutations,
  canBindVideo,
}: {
  detail: CatalogNodeDetail;
  mediaAssets: UseQueryResult<ApiList<MediaAsset>>;
  mutations: CatalogMutations;
  canBindVideo: boolean;
}) {
  const { node } = detail;
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pendingMediaId, setPendingMediaId] = useState<string | null>(null);
  const currentVideo = detail.media_bindings[0] || null;

  if (!isPointCapable(node.node_kind)) {
    return (
      <section className="catalog-editor-section catalog-editor-panel-section">
        <Title level={4}>视频绑定</Title>
        <Text type="secondary">目录节点不绑定视频，请选择点位节点维护视频素材。</Text>
      </section>
    );
  }

  const bindVideo = (asset: MediaAsset) => {
    setPendingMediaId(asset.id);
    mutations.bindMedia.mutate(
      { nodeId: node.node_id, asset },
      {
        onSuccess: () => setPickerOpen(false),
        onSettled: () => setPendingMediaId(null),
      },
    );
  };

  const removeVideo = () => {
    if (!currentVideo) return;
    mutations.changeMediaStatus.mutate({ bindingId: currentVideo.binding_id, action: "delete" });
  };

  return (
    <section className="catalog-editor-section catalog-editor-panel-section">
      <div className="catalog-video-panel-heading">
        <div>
          <Title level={4}>视频绑定</Title>
          <Text type="secondary">当前视频会出现在学生学习卡片中；新视频请先到视频资源页上传处理。</Text>
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
      {!canBindVideo ? <Text type="secondary">请先补全点位学习内容，再绑定实验视频。</Text> : null}
      <CurrentVideoSlot
        binding={currentVideo}
        canBindVideo={canBindVideo}
        onOpenPicker={() => setPickerOpen(true)}
        onRemove={removeVideo}
        removing={mutations.changeMediaStatus.isPending}
      />
      <CatalogVideoPicker
        open={pickerOpen}
        currentMediaId={currentVideo?.media_id}
        mediaAssets={mediaAssets}
        pendingMediaId={pendingMediaId}
        onCancel={() => setPickerOpen(false)}
        onSelect={bindVideo}
      />
    </section>
  );
}
