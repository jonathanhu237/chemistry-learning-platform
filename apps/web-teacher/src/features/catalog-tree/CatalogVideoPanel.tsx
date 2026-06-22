import { useMemo, useState } from "react";
import { Button, Empty, Input, Modal, Popconfirm, Tag, Typography } from "antd";
import {
  ArrowRightOutlined,
  EyeOutlined,
  LinkOutlined,
  PlayCircleFilled,
  SearchOutlined,
  SwapOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";
import type { UseQueryResult } from "@tanstack/react-query";

import type { ApiList } from "../../api/common";
import type { CatalogMediaBinding, CatalogNodeDetail } from "../../api/catalogTree";
import { getMediaAssetFileUrl, getMediaAssetThumbnailUrl, type MediaAsset } from "../../api/media";
import { formatBytes } from "../../lib/format";
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

function formatPlaybackResolution(binding: CatalogMediaBinding): string | null {
  if (!binding.playback_width || !binding.playback_height) return null;
  return `${binding.playback_width} x ${binding.playback_height}`;
}

function formatUploadTimestamp(value?: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  const pad = (part: number) => String(part).padStart(2, "0");
  return [
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`,
  ].join(" ");
}

function buildCurrentVideoFacts(binding: CatalogMediaBinding): string {
  const facts: string[] = [];
  if (binding.playback_file_size_bytes && binding.playback_file_size_bytes > 0) {
    facts.push(`学生播放源 ${formatBytes(binding.playback_file_size_bytes)}`);
  } else {
    facts.push("学生播放源大小待生成");
  }
  const resolution = formatPlaybackResolution(binding);
  if (resolution) facts.push(resolution);
  const uploadedAt = formatUploadTimestamp(binding.created_at);
  if (uploadedAt) facts.push(`上传 ${uploadedAt}`);
  return facts.join(" · ");
}

function formatCurrentVideoDuration(seconds?: number | null): string | null {
  if (!seconds || seconds <= 0) return null;
  const total = Math.round(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  if (hours > 0) return `${hours}:${String(minutes % 60).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

function formatCurrentVideoFps(value?: number | null): string | null {
  if (!value || value <= 0) return null;
  return `${Number(value).toFixed(3)} fps`;
}

function formatCurrentVideoBitrate(value?: number | null): string | null {
  if (!value || value <= 0) return null;
  const kbps = Number(value) / 1000;
  if (!Number.isFinite(kbps) || kbps <= 0) return null;
  if (kbps >= 1000) return `${(kbps / 1000).toFixed(2)} Mbps`;
  return `${Math.round(kbps).toLocaleString()} Kbps`;
}

function buildCurrentVideoFactRows(binding: CatalogMediaBinding): Array<{ label: string; value: string }> {
  const facts: Array<{ label: string; value: string }> = [
    { label: "播放源", value: binding.playback_rendition_kind === "learning" ? "学生播放源" : "学生可播放源" },
  ];
  facts.push({
    label: "文件大小",
    value:
      binding.playback_file_size_bytes && binding.playback_file_size_bytes > 0
        ? formatBytes(binding.playback_file_size_bytes)
        : "学生播放源大小待生成",
  });
  if (
    binding.source_file_size_bytes &&
    binding.playback_file_size_bytes &&
    binding.source_file_size_bytes > 0 &&
    binding.source_file_size_bytes !== binding.playback_file_size_bytes
  ) {
    facts.push({ label: "原始大小", value: formatBytes(binding.source_file_size_bytes) });
  }
  if (binding.playback_width && binding.playback_height) {
    const fps = formatCurrentVideoFps(binding.playback_fps);
    facts.push({ label: "分辨率", value: `${binding.playback_width} x ${binding.playback_height}${fps ? ` @ ${fps}` : ""}` });
  }
  const bitrate = formatCurrentVideoBitrate(binding.playback_bitrate);
  if (bitrate) facts.push({ label: "码率", value: bitrate });
  if (binding.playback_video_codec) facts.push({ label: "视频编码", value: binding.playback_video_codec });
  if (binding.playback_audio_codec) facts.push({ label: "音频编码", value: binding.playback_audio_codec });
  if (binding.playback_mime_type) facts.push({ label: "Mime Type", value: binding.playback_mime_type });
  const duration = formatCurrentVideoDuration(binding.playback_duration_seconds);
  if (duration) facts.push({ label: "时长", value: duration });
  const uploadedAt = formatUploadTimestamp(binding.created_at);
  if (uploadedAt) facts.push({ label: "上传时间", value: uploadedAt });
  return facts;
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
  onOpenContentTask,
  onRemove,
  removing,
}: {
  binding?: CatalogMediaBinding | null;
  canBindVideo: boolean;
  onOpenPicker: () => void;
  onOpenContentTask?: () => void;
  onRemove: () => void;
  removing: boolean;
}) {
  const [previewOpen, setPreviewOpen] = useState(false);

  if (!binding) {
    if (!canBindVideo) {
      return (
        <div className="catalog-video-empty-slot is-blocked" role="status">
          <span className="catalog-video-empty-icon" aria-hidden="true">
            <VideoCameraOutlined />
          </span>
          <span className="catalog-video-empty-copy">
            <strong>先完善学习内容</strong>
            <small>补全学习字段后即可绑定实验视频。</small>
            {onOpenContentTask ? (
              <button type="button" className="catalog-video-inline-link" onClick={onOpenContentTask}>
                编辑内容
              </button>
            ) : null}
          </span>
        </div>
      );
    }

    return (
      <button
        type="button"
        className="catalog-video-empty-slot"
        onClick={onOpenPicker}
      >
        <span className="catalog-video-empty-icon" aria-hidden="true">
          <VideoCameraOutlined />
        </span>
        <span className="catalog-video-empty-copy">
          <strong>选择视频素材</strong>
          <small>从视频资源中选择一个已就绪视频，选择后自动绑定</small>
        </span>
      </button>
    );
  }

  const mediaUrl = getMediaAssetFileUrl(binding.media_id);
  const posterUrl = binding.has_thumbnail ? getMediaAssetThumbnailUrl(binding.media_id) : undefined;
  const currentVideoFacts = buildCurrentVideoFactRows(binding);

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
            <dl className="catalog-video-current-facts">
              {currentVideoFacts.map((fact) => (
                <div className="catalog-video-current-fact" key={fact.label}>
                  <dt>{fact.label}</dt>
                  <dd>{fact.value}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="catalog-video-current-actions">
            <Button className="catalog-video-card-action" icon={<SwapOutlined />} onClick={onOpenPicker} disabled={!canBindVideo}>
              更换视频
            </Button>
            <Popconfirm title="解绑当前视频？" onConfirm={onRemove}>
              <Button className="catalog-video-card-action is-danger" danger icon={<LinkOutlined />} loading={removing}>
                解绑视频
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
  const readyAssetCount = assets.filter(isReadyVideo).length;

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
      {!readyAssetCount ? (
        <a className="catalog-video-picker-resource-entry" href="/videos">
          <span>
            <strong>没有可绑定的就绪视频</strong>
            <small>去视频资源页上传或等待处理完成</small>
          </span>
          <ArrowRightOutlined />
        </a>
      ) : null}
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
  pickerOpen,
  onPickerOpenChange,
  onOpenContentTask,
}: {
  detail: CatalogNodeDetail;
  mediaAssets: UseQueryResult<ApiList<MediaAsset>>;
  mutations: CatalogMutations;
  canBindVideo: boolean;
  pickerOpen?: boolean;
  onPickerOpenChange?: (open: boolean) => void;
  onOpenContentTask?: () => void;
}) {
  const { node } = detail;
  const [internalPickerOpen, setInternalPickerOpen] = useState(false);
  const [pendingMediaId, setPendingMediaId] = useState<string | null>(null);
  const currentVideo = detail.media_bindings[0] || null;
  const resolvedPickerOpen = pickerOpen ?? internalPickerOpen;
  const setPickerOpen = (open: boolean) => {
    if (onPickerOpenChange) {
      onPickerOpenChange(open);
      return;
    }
    setInternalPickerOpen(open);
  };

  if (!isPointCapable(node.node_kind)) {
    return (
      <section className="catalog-editor-section catalog-editor-panel-section">
        <Title level={4}>实验视频</Title>
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
    <section className="catalog-editor-section catalog-editor-panel-section catalog-video-panel-section">
      <div className="catalog-video-panel-heading">
        <div>
          <Title level={4}>实验视频</Title>
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
      <CurrentVideoSlot
        binding={currentVideo}
        canBindVideo={canBindVideo}
        onOpenPicker={() => setPickerOpen(true)}
        onOpenContentTask={onOpenContentTask}
        onRemove={removeVideo}
        removing={mutations.changeMediaStatus.isPending}
      />
      <CatalogVideoPicker
        open={resolvedPickerOpen}
        currentMediaId={currentVideo?.media_id}
        mediaAssets={mediaAssets}
        pendingMediaId={pendingMediaId}
        onCancel={() => setPickerOpen(false)}
        onSelect={bindVideo}
      />
    </section>
  );
}
