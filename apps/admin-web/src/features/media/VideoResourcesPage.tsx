import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Descriptions,
  Divider,
  Empty,
  Flex,
  Input,
  Modal,
  Progress,
  Segmented,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
  Upload,
} from "antd";
import {
  AppstoreOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  UnorderedListOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";
import type Uppy from "@uppy/core";

import { api, apiBase, formatBytes, getAuthToken, patchJson, postJson } from "../../api";
import type { ApiList, MediaAsset, MediaDuplicatePrecheck } from "../../api";
import { AuthenticatedImage } from "../../components/AuthenticatedImage";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { errorMessage } from "../../lib/errors";
import { isPreviewableVideo, mediaAssetTime, mediaAssetType } from "../resources/resourceUtils";
import "./media.css";

const { Text, Title } = Typography;

type VideoUploadStage =
  | "idle"
  | "pending"
  | "hashing"
  | "ready"
  | "duplicate"
  | "uploading"
  | "paused"
  | "finalizing"
  | "processing"
  | "complete"
  | "error";

type VideoUploadState = {
  stage: VideoUploadStage;
  hashProgress: number;
  progress: number;
  uploadedBytes: number;
  totalBytes: number;
  checksum?: string;
  duplicateAsset?: MediaAsset | null;
  error?: string;
  note?: string;
};

type VideoUploadQueueItem = {
  id: string;
  file: File;
  title: string;
  status: VideoUploadStage;
  hashProgress: number;
  progress: number;
  uploadedBytes: number;
  totalBytes: number;
  checksum?: string;
  duplicateAsset?: MediaAsset | null;
  error?: string;
  note?: string;
};

const emptyUploadState: VideoUploadState = {
  stage: "idle",
  hashProgress: 0,
  progress: 0,
  uploadedBytes: 0,
  totalBytes: 0,
};

const mediaStatusLabels: Record<string, string> = {
  pending: "待处理",
  processing: "处理中",
  ready: "就绪",
  failed: "处理失败",
  replaced: "已替换",
};

const mediaStatusColors: Record<string, string> = {
  pending: "#b8892f",
  processing: "#356f9c",
  ready: "#005826",
  failed: "#b42318",
  replaced: "default",
};

const processingPhaseLabels: Record<string, string> = {
  queued: "已排队",
  starting: "启动中",
  validating: "校验文件",
  probing: "读取元数据",
  thumbnailing: "生成缩略图",
  transcoding: "生成学生播放源",
  fingerprinting: "生成相似度签名",
  comparing: "比对相似视频",
  ready: "已就绪",
  failed: "处理失败",
};

const duplicateDecisionLabels: Record<string, string> = {
  pending: "待确认",
  kept: "已保留",
  reused: "已复用",
  ignored: "已忽略",
};

function mediaStatusTag(status?: string) {
  const value = status || "pending";
  return <Tag color={mediaStatusColors[value] || "default"}>{mediaStatusLabels[value] || value}</Tag>;
}

function processingPhaseText(asset?: MediaAsset | null): string {
  const phase = asset?.processing_phase || asset?.processing_job?.phase || asset?.upload_status || "";
  return processingPhaseLabels[phase] || phase || "-";
}

function processingProgressValue(asset?: MediaAsset | null): number {
  return Math.max(0, Math.min(100, Number(asset?.processing_progress ?? asset?.processing_job?.progress ?? 0)));
}

function formatDurationSeconds(value?: number | null): string {
  if (!value) return "-";
  const total = Math.round(Number(value));
  const minutes = Math.floor(total / 60);
  const seconds = String(total % 60).padStart(2, "0");
  if (minutes < 60) return String(minutes) + ":" + seconds;
  const hours = Math.floor(minutes / 60);
  return String(hours) + ":" + String(minutes % 60).padStart(2, "0") + ":" + seconds;
}

function formatResolution(asset?: { width?: number | null; height?: number | null } | null): string {
  return asset?.width && asset?.height ? String(asset.width) + " x " + String(asset.height) : "-";
}

function selectedRendition(asset: MediaAsset) {
  return asset.renditions?.find((rendition) => rendition.kind === "learning") || asset.renditions?.[0];
}

function renditionSavings(asset: MediaAsset) {
  const rendition = selectedRendition(asset);
  const sourceSize = Number(asset.file_size_bytes || 0);
  const renditionSize = Number(rendition?.file_size_bytes || 0);
  const savedBytes = sourceSize && renditionSize ? Math.max(0, sourceSize - renditionSize) : 0;
  const savedPercent = sourceSize && savedBytes ? Math.round((savedBytes / sourceSize) * 100) : 0;
  return { rendition, savedBytes, savedPercent };
}

function pendingDuplicateCandidates(asset?: MediaAsset | null) {
  return (asset?.duplicate_candidates || []).filter((candidate) => candidate.status === "pending");
}

function hasPendingDuplicate(asset?: MediaAsset | null): boolean {
  return pendingDuplicateCandidates(asset).length > 0;
}

function duplicateScoreText(score?: number | null): string {
  if (score == null) return "-";
  const value = Number(score);
  if (!Number.isFinite(value)) return "-";
  return value > 1 ? value.toFixed(1) + "%" : Math.round(value * 100) + "%";
}

function uploadStepCurrent(stage: VideoUploadStage): number {
  if (["uploading", "paused", "finalizing"].includes(stage)) return 1;
  if (["processing", "complete"].includes(stage)) return 2;
  return 0;
}

function uploadStageText(stage: VideoUploadStage): string {
  if (stage === "pending") return "已加入队列，点击开始后会按顺序上传";
  if (stage === "hashing") return "正在做 SHA-256 完全重复校验";
  if (stage === "duplicate") return "发现完全相同的已上传文件";
  if (stage === "ready") return "文件已就绪，可以开始上传";
  if (stage === "uploading") return "正在上传文件";
  if (stage === "paused") return "上传已暂停，可继续断点续传";
  if (stage === "finalizing") return "正在完成入库并交给后台";
  if (stage === "processing") return "上传完成，后台正在处理";
  if (stage === "complete") return "上传已完成，已加入后台处理队列";
  if (stage === "error") return "上传遇到问题";
  return "选择视频后会先校验，再上传";
}

function videoTitleFromFile(file: File): string {
  return file.name.replace(/\.[^.]+$/, "").trim() || file.name;
}

function uploadQueueItemText(item: VideoUploadQueueItem): string {
  if (item.status === "pending") return "等待上传";
  if (item.status === "hashing") return "校验重复 " + item.hashProgress + "%";
  if (item.status === "ready") return "准备上传";
  if (item.status === "duplicate") return "完全重复，已复用";
  if (item.status === "uploading") return "上传中 " + item.progress + "%";
  if (item.status === "paused") return "已暂停";
  if (item.status === "finalizing") return "正在入库";
  if (item.status === "processing") return "已交给后台处理";
  if (item.status === "complete") return "已完成";
  if (item.status === "error") return item.error || "上传失败";
  return uploadStageText(item.status);
}

async function computeVideoFileSha256(file: File, onProgress: (progress: number) => void): Promise<string> {
  const { createSHA256 } = await import("hash-wasm");
  const hasher = await createSHA256();
  hasher.init();
  const chunkSize = 8 * 1024 * 1024;
  let offset = 0;
  while (offset < file.size) {
    const nextOffset = Math.min(offset + chunkSize, file.size);
    const chunk = new Uint8Array(await file.slice(offset, nextOffset).arrayBuffer());
    hasher.update(chunk);
    offset = nextOffset;
    onProgress(file.size ? Math.round((offset / file.size) * 100) : 100);
    await new Promise((resolve) => window.setTimeout(resolve, 0));
  }
  return hasher.digest("hex");
}

function extractTusUploadId(uploadUrl?: string | null): string {
  if (!uploadUrl) return "";
  try {
    const url = new URL(uploadUrl, window.location.href);
    const parts = url.pathname.split("/").filter(Boolean);
    return decodeURIComponent(parts[parts.length - 1] || "");
  } catch {
    const parts = uploadUrl.split("/").filter(Boolean);
    return decodeURIComponent(parts[parts.length - 1] || "");
  }
}

function MediaThumbnail({ asset, compact = false }: { asset: MediaAsset; compact?: boolean }) {
  const src = asset.thumbnail_relative_path ? apiBase + "/api/admin/media/assets/" + asset.id + "/thumbnail" : null;
  const className = compact ? "video-thumb-image compact" : "video-thumb-image";
  return (
    <div className={compact ? "video-thumb-frame compact" : "video-thumb-frame"}>
      <AuthenticatedImage src={src} alt={asset.title} className={className} />
      <div className="video-thumb-fallback">
        <VideoCameraOutlined />
        <span>{asset.thumbnail_relative_path ? "缩略图" : asset.upload_status === "ready" ? mediaAssetType(asset) : processingPhaseText(asset)}</span>
      </div>
    </div>
  );
}

export function VideoResourcesPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const assets = useQuery({
    queryKey: ["media-assets"],
    queryFn: () => api<ApiList<MediaAsset>>("/api/admin/media/assets?limit=200"),
  });
  const tusEndpoint = String(import.meta.env.VITE_TUS_ENDPOINT || "").trim().replace(/\/+$/, "");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>();
  const [sortKey, setSortKey] = useState<"updated_desc" | "name_asc" | "size_desc">("updated_desc");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadItems, setUploadItems] = useState<VideoUploadQueueItem[]>([]);
  const [currentUploadId, setCurrentUploadId] = useState<string>();
  const [batchRunning, setBatchRunning] = useState(false);
  const [uploadState, setUploadState] = useState<VideoUploadState>(emptyUploadState);
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>();
  const [previewPosterUrl, setPreviewPosterUrl] = useState<string>();
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const uppyRef = useRef<Uppy | null>(null);
  const uppyFileIdRef = useRef("");
  const xhrRef = useRef<XMLHttpRequest | null>(null);
  const hashRunRef = useRef(0);
  const uploadItemsRef = useRef<VideoUploadQueueItem[]>([]);
  const currentUploadIdRef = useRef<string | undefined>(undefined);
  const cancelBatchRef = useRef(false);

  const assetItems = useMemo(() => assets.data?.items || [], [assets.data?.items]);
  const readyAssets = useMemo(() => assetItems.filter((asset) => asset.upload_status === "ready"), [assetItems]);
  const workingAssets = useMemo(
    () => assetItems.filter((asset) => ["pending", "processing"].includes(asset.upload_status)),
    [assetItems],
  );
  const failedAssets = useMemo(() => assetItems.filter((asset) => asset.upload_status === "failed"), [assetItems]);
  const pendingDuplicateAssets = useMemo(() => assetItems.filter((asset) => hasPendingDuplicate(asset)), [assetItems]);
  const sourceBytes = useMemo(
    () => assetItems.reduce((sum, asset) => sum + Number(asset.file_size_bytes || 0), 0),
    [assetItems],
  );
  const renditionBytes = useMemo(
    () => assetItems.reduce((sum, asset) => sum + (asset.renditions || []).reduce((subtotal, rendition) => subtotal + Number(rendition.file_size_bytes || 0), 0), 0),
    [assetItems],
  );
  const savedBytes = Math.max(0, sourceBytes - renditionBytes);
  const savedPercent = sourceBytes > 0 && renditionBytes > 0 ? Math.round((savedBytes / sourceBytes) * 100) : 0;
  const currentUploadItem = useMemo(
    () => uploadItems.find((item) => item.id === currentUploadId) || null,
    [currentUploadId, uploadItems],
  );
  const uploadQueueDoneCount = useMemo(
    () => uploadItems.filter((item) => ["duplicate", "processing", "complete"].includes(item.status)).length,
    [uploadItems],
  );
  const uploadQueueTotalBytes = useMemo(() => uploadItems.reduce((sum, item) => sum + item.totalBytes, 0), [uploadItems]);
  const uploadQueueUploadedBytes = useMemo(() => uploadItems.reduce((sum, item) => sum + item.uploadedBytes, 0), [uploadItems]);
  const uploadQueueProgress = uploadQueueTotalBytes ? Math.round((uploadQueueUploadedBytes / uploadQueueTotalBytes) * 100) : 0;
  const hasActiveWork = workingAssets.length > 0 || batchRunning || uploadItems.some((item) => ["uploading", "paused", "finalizing", "hashing"].includes(item.status));
  const filteredAssets = useMemo(() => {
    const normalized = keyword.trim().toLowerCase();
    const list = assetItems.filter((asset) => {
      if (statusFilter === "duplicate_pending" && !hasPendingDuplicate(asset)) return false;
      if (statusFilter && statusFilter !== "duplicate_pending" && asset.upload_status !== statusFilter) return false;
      if (!normalized) return true;
      return (asset.title + " " + asset.original_file_name).toLowerCase().includes(normalized);
    });
    return [...list].sort((left, right) => {
      if (sortKey === "name_asc") return left.title.localeCompare(right.title, "zh-Hans-CN");
      if (sortKey === "size_desc") return Number(right.file_size_bytes || 0) - Number(left.file_size_bytes || 0);
      const rightTime = new Date(right.updated_at || right.created_at || "").getTime() || 0;
      const leftTime = new Date(left.updated_at || left.created_at || "").getTime() || 0;
      return rightTime - leftTime;
    });
  }, [assetItems, keyword, sortKey, statusFilter]);

  useEffect(() => {
    uploadItemsRef.current = uploadItems;
  }, [uploadItems]);

  useEffect(() => {
    if (!hasActiveWork) return undefined;
    const timer = window.setInterval(() => {
      void queryClient.invalidateQueries({ queryKey: ["media-assets"] });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [hasActiveWork, queryClient]);

  useEffect(() => {
    let posterObjectUrl: string | undefined;
    let cancelled = false;
    setPreviewUrl(undefined);
    setPreviewPosterUrl(undefined);
    setPreviewError("");
    setPreviewLoading(false);
    if (!previewAsset || !isPreviewableVideo(previewAsset)) return undefined;
    setPreviewLoading(true);
    const headers = new Headers();
    const token = getAuthToken();
    if (token) headers.set("Authorization", "Bearer " + token);
    if (!token) {
      setPreviewError("登录状态已失效，请重新登录后预览视频");
      setPreviewLoading(false);
      return undefined;
    }
    setPreviewUrl(apiBase + "/api/admin/media/assets/" + previewAsset.id + "/stream?access_token=" + encodeURIComponent(token));
    setPreviewLoading(false);
    if (previewAsset.thumbnail_relative_path) {
      void fetch(apiBase + "/api/admin/media/assets/" + previewAsset.id + "/thumbnail", { headers })
        .then((response) => {
          if (!response.ok) throw new Error("poster_load_failed");
          return response.blob();
        })
        .then((blob) => {
          if (cancelled) return;
          posterObjectUrl = URL.createObjectURL(blob);
          setPreviewPosterUrl(posterObjectUrl);
        })
        .catch(() => {
          if (!cancelled) setPreviewPosterUrl(undefined);
        });
    }
    return () => {
      cancelled = true;
      if (posterObjectUrl) URL.revokeObjectURL(posterObjectUrl);
    };
  }, [previewAsset]);

  useEffect(() => {
    return () => {
      uppyRef.current?.destroy();
      xhrRef.current?.abort();
    };
  }, []);

  const invalidateVideoData = () => {
    void queryClient.invalidateQueries({ queryKey: ["media-assets"] });
  };

  const disposeUploadClient = () => {
    uppyRef.current?.destroy();
    uppyRef.current = null;
    uppyFileIdRef.current = "";
    xhrRef.current?.abort();
    xhrRef.current = null;
  };

  const resetUploadModal = () => {
    hashRunRef.current += 1;
    cancelBatchRef.current = true;
    disposeUploadClient();
    setUploadTitle("");
    uploadItemsRef.current = [];
    currentUploadIdRef.current = undefined;
    setUploadItems([]);
    setCurrentUploadId(undefined);
    setBatchRunning(false);
    setUploadState(emptyUploadState);
  };

  const makeUploadQueueItem = (file: File, id?: string): VideoUploadQueueItem => ({
    id: id || `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2)}`,
    file,
    title: videoTitleFromFile(file),
    status: "pending",
    hashProgress: 0,
    progress: 0,
    uploadedBytes: 0,
    totalBytes: file.size,
  });

  const updateUploadItem = (itemId: string, patch: Partial<VideoUploadQueueItem>) => {
    const nextItems = uploadItemsRef.current.map((item) => (item.id === itemId ? { ...item, ...patch } : item));
    uploadItemsRef.current = nextItems;
    setUploadItems(nextItems);
  };

  const setActiveUploadItemState = (itemId: string, patch: Partial<VideoUploadQueueItem>) => {
    updateUploadItem(itemId, patch);
    setUploadState((current) => ({
      ...current,
      stage: patch.status || current.stage,
      hashProgress: patch.hashProgress ?? current.hashProgress,
      progress: patch.progress ?? current.progress,
      uploadedBytes: patch.uploadedBytes ?? current.uploadedBytes,
      totalBytes: patch.totalBytes ?? current.totalBytes,
      checksum: patch.checksum ?? current.checksum,
      duplicateAsset: patch.duplicateAsset !== undefined ? patch.duplicateAsset : current.duplicateAsset,
      error: patch.error,
      note: patch.note,
    }));
  };

  const handleUploadFiles = (files: File[]) => {
    if (batchRunning) {
      message.warning("队列正在上传，请先暂停或取消当前队列");
      return;
    }
    hashRunRef.current += 1;
    disposeUploadClient();
    const videoFiles = files.filter((file) => file.type.startsWith("video/") || /\.(mp4|mov|m4v|webm|avi)$/i.test(file.name));
    const nextItems = videoFiles.map((file) => makeUploadQueueItem(file, (file as File & { uid?: string }).uid));
    uploadItemsRef.current = nextItems;
    currentUploadIdRef.current = undefined;
    setUploadItems(nextItems);
    setCurrentUploadId(undefined);
    setUploadTitle(nextItems.length === 1 ? nextItems[0].title : "");
    setUploadState({
      ...emptyUploadState,
      stage: nextItems.length ? "pending" : "idle",
      totalBytes: nextItems.reduce((sum, item) => sum + item.totalBytes, 0),
      note: nextItems.length > 1 ? `已选择 ${nextItems.length} 个视频，将按顺序逐个上传。` : undefined,
    });
    if (files.length && !videoFiles.length) {
      message.warning("请选择视频文件");
    }
  };

  const updateSingleUploadTitle = (value: string) => {
    setUploadTitle(value);
    if (uploadItems.length === 1) {
      updateUploadItem(uploadItems[0].id, { title: value });
    }
  };

  const runDuplicatePrecheck = async (item: VideoUploadQueueItem) => {
    const runId = hashRunRef.current;
    setActiveUploadItemState(item.id, {
      status: "hashing",
      hashProgress: 0,
      progress: 0,
      uploadedBytes: 0,
      totalBytes: item.file.size,
      error: undefined,
      note: undefined,
      duplicateAsset: null,
    });
    try {
      const checksum = await computeVideoFileSha256(item.file, (progress) => {
        if (hashRunRef.current !== runId) return;
        setActiveUploadItemState(item.id, { hashProgress: progress });
      });
      if (hashRunRef.current !== runId || cancelBatchRef.current) return { checksum: undefined, duplicateAsset: null };
      const precheck = await postJson<MediaDuplicatePrecheck>("/api/admin/media/assets/precheck", {
        checksum_sha256: checksum,
        file_size_bytes: item.file.size,
      });
      if (hashRunRef.current !== runId || cancelBatchRef.current) return { checksum, duplicateAsset: null };
      setActiveUploadItemState(item.id, {
        status: precheck.exists && precheck.asset ? "duplicate" : "ready",
        hashProgress: 100,
        totalBytes: item.file.size,
        checksum,
        duplicateAsset: precheck.asset || null,
        note: precheck.exists && precheck.asset ? "发现完全相同的已上传文件，已复用已有视频。" : undefined,
      });
      return { checksum, duplicateAsset: precheck.asset || null };
    } catch (error) {
      if (hashRunRef.current !== runId || cancelBatchRef.current) return { checksum: undefined, duplicateAsset: null };
      setActiveUploadItemState(item.id, {
        status: "ready",
        totalBytes: item.file.size,
        note: "预检未完成：" + errorMessage(error),
      });
      return { checksum: undefined, duplicateAsset: null };
    }
  };

  const finalizeResumableUpload = async (item: VideoUploadQueueItem, uploadUrl?: string | null, checksum?: string) => {
    const uploadId = extractTusUploadId(uploadUrl);
    if (!uploadId) throw new Error("无法识别 tus 上传编号");
    setActiveUploadItemState(item.id, { status: "finalizing", progress: 100, uploadedBytes: item.file.size, totalBytes: item.file.size });
    const asset = await postJson<MediaAsset>("/api/admin/media/assets/complete-upload", {
      title: item.title.trim() || videoTitleFromFile(item.file),
      upload_id: uploadId,
      filename: item.file.name,
      content_type: item.file.type || "video/mp4",
      checksum_sha256: checksum || undefined,
    });
    setActiveUploadItemState(item.id, {
      status: asset.upload_status === "ready" ? "complete" : "processing",
      progress: 100,
      uploadedBytes: item.file.size,
      totalBytes: item.file.size,
      note: asset.upload_status === "ready" ? "已复用已有视频" : "已进入后台处理",
    });
    invalidateVideoData();
  };

  const uploadItemWithTus = async (item: VideoUploadQueueItem, checksum?: string) => {
    if (!tusEndpoint) throw new Error("未配置 tus 上传端点");
    disposeUploadClient();
    const [{ default: Uppy }, { default: Tus }] = await Promise.all([
      import("@uppy/core"),
      import("@uppy/tus"),
    ]);
    const uppy = new Uppy({ autoProceed: false, restrictions: { maxNumberOfFiles: 1 } });
    uppy.use(Tus, {
      endpoint: tusEndpoint + "/",
      chunkSize: 10 * 1024 * 1024,
      retryDelays: [0, 1000, 3000, 5000],
      storeFingerprintForResuming: true,
      removeFingerprintOnSuccess: false,
      metadata: {
        filename: item.file.name,
        filetype: item.file.type || "video/mp4",
      },
    });
    uppyFileIdRef.current = uppy.addFile({ name: item.file.name, type: item.file.type || "video/mp4", data: item.file });
    uppyRef.current = uppy;
    setActiveUploadItemState(item.id, { status: "uploading", progress: 0, uploadedBytes: 0, totalBytes: item.file.size, error: undefined });
    await new Promise<void>((resolve, reject) => {
      let settled = false;
      const settle = (fn: () => void) => {
        if (settled) return;
        settled = true;
        fn();
      };
      uppy.on("upload-progress", (_file, progress) => {
        const uploadedBytes = Number(progress.bytesUploaded || 0);
        const totalBytes = Number(progress.bytesTotal || item.file.size || 0);
        setActiveUploadItemState(item.id, {
          status: "uploading",
          uploadedBytes,
          totalBytes,
          progress: totalBytes ? Math.round((uploadedBytes / totalBytes) * 100) : item.progress,
        });
      });
      uppy.on("upload-error", (_file, error) => {
        settle(() => reject(error));
      });
      uppy.on("upload-success", (file, response) => {
        const uploadUrl = response.uploadURL || (file as unknown as { uploadURL?: string }).uploadURL;
        void finalizeResumableUpload(item, uploadUrl, checksum).then(() => settle(resolve)).catch((error) => settle(() => reject(error)));
      });
      void uppy.upload().catch((error) => settle(() => reject(error)));
    });
  };

  const uploadItemWithFallback = async (item: VideoUploadQueueItem, checksum?: string) => {
    disposeUploadClient();
    const body = new FormData();
    body.append("title", item.title.trim() || videoTitleFromFile(item.file));
    body.append("file", item.file);
    if (checksum) body.append("checksum_sha256", checksum);
    setActiveUploadItemState(item.id, { status: "uploading", progress: 0, uploadedBytes: 0, totalBytes: item.file.size, error: undefined });
    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhrRef.current = xhr;
      xhr.open("POST", apiBase + "/api/admin/media/assets");
      const token = getAuthToken();
      if (token) xhr.setRequestHeader("Authorization", "Bearer " + token);
      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) return;
        setActiveUploadItemState(item.id, {
          status: "uploading",
          uploadedBytes: event.loaded,
          totalBytes: event.total,
          progress: Math.round((event.loaded / event.total) * 100),
        });
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const asset = JSON.parse(xhr.responseText || "{}") as MediaAsset;
          setActiveUploadItemState(item.id, {
            status: asset.upload_status === "ready" ? "complete" : "processing",
            progress: 100,
            uploadedBytes: item.file.size,
            totalBytes: item.file.size,
            note: asset.upload_status === "ready" ? "已复用已有视频" : "已进入后台处理",
          });
          invalidateVideoData();
          resolve();
        } else {
          reject(new Error(xhr.responseText || "HTTP " + xhr.status));
        }
      };
      xhr.onerror = () => reject(new Error("上传失败"));
      xhr.onabort = () => reject(new Error("上传已取消"));
      xhr.send(body);
    });
  };

  const processUploadItem = async (item: VideoUploadQueueItem) => {
    currentUploadIdRef.current = item.id;
    setCurrentUploadId(item.id);
    const title = item.title.trim() || videoTitleFromFile(item.file);
    updateUploadItem(item.id, { title });
    const precheck = await runDuplicatePrecheck({ ...item, title });
    if (cancelBatchRef.current) return;
    if (precheck.duplicateAsset) {
      setActiveUploadItemState(item.id, {
        status: "duplicate",
        progress: 100,
        uploadedBytes: item.file.size,
        totalBytes: item.file.size,
        duplicateAsset: precheck.duplicateAsset,
        note: "完全相同文件已存在，未重复上传。",
      });
      invalidateVideoData();
      return;
    }
    const itemForUpload = { ...item, title };
    if (tusEndpoint) await uploadItemWithTus(itemForUpload, precheck.checksum);
    else await uploadItemWithFallback(itemForUpload, precheck.checksum);
  };

  const startUpload = async () => {
    if (!uploadItems.length) {
      message.warning("请先选择视频文件");
      return;
    }
    if (uploadItems.length === 1 && !uploadItems[0].title.trim()) {
      message.warning("请输入视频标题");
      return;
    }
    cancelBatchRef.current = false;
    hashRunRef.current += 1;
    setBatchRunning(true);
    try {
      const queue = uploadItemsRef.current.filter((item) => ["pending", "ready", "error"].includes(item.status));
      for (const queuedItem of queue) {
        if (cancelBatchRef.current) break;
        const latest = uploadItemsRef.current.find((item) => item.id === queuedItem.id) || queuedItem;
        await processUploadItem(latest);
      }
      disposeUploadClient();
      currentUploadIdRef.current = undefined;
      setCurrentUploadId(undefined);
      if (cancelBatchRef.current) {
        setUploadState((current) => ({ ...current, stage: uploadItemsRef.current.length ? "pending" : "idle", note: "上传队列已取消" }));
      } else {
        setUploadState((current) => ({ ...current, stage: "complete", progress: 100, note: `队列已处理 ${uploadItemsRef.current.length} 个视频，后台会继续生成缩略图和学生播放源。` }));
        message.success("上传队列已处理完成");
        invalidateVideoData();
      }
    } catch (error) {
      const failedItemId = currentUploadIdRef.current || currentUploadId;
      if (failedItemId) updateUploadItem(failedItemId, { status: "error", error: errorMessage(error) });
      setUploadState((current) => ({ ...current, stage: "error", error: errorMessage(error), note: "队列已暂停，修复后可点击重试继续。" }));
      message.error(errorMessage(error));
    } finally {
      setBatchRunning(false);
    }
  };

  const toggleUploadPause = () => {
    if (!uppyRef.current || !uppyFileIdRef.current) return;
    const paused = uppyRef.current.pauseResume(uppyFileIdRef.current);
    const activeItemId = currentUploadIdRef.current || currentUploadId;
    if (activeItemId) updateUploadItem(activeItemId, { status: paused ? "paused" : "uploading" });
    setUploadState((current) => ({ ...current, stage: paused ? "paused" : "uploading" }));
  };

  const retryUpload = () => {
    if (uppyRef.current && uppyFileIdRef.current) {
      setUploadState((current) => ({ ...current, stage: "uploading", error: undefined }));
      void uppyRef.current.retryUpload(uppyFileIdRef.current);
      return;
    }
    void startUpload();
  };

  const cancelUpload = () => {
    cancelBatchRef.current = true;
    disposeUploadClient();
    setBatchRunning(false);
    const activeItemId = currentUploadIdRef.current || currentUploadId;
    if (activeItemId) {
      updateUploadItem(activeItemId, { status: "error", error: "已取消，可重新开始队列" });
    }
    currentUploadIdRef.current = undefined;
    setUploadState((current) => ({ ...current, stage: uploadItems.length ? "pending" : "idle", progress: 0, uploadedBytes: 0, note: "上传队列已取消" }));
  };

  const reuseDuplicate = () => {
    if (!currentUploadItem?.duplicateAsset && !uploadState.duplicateAsset) return;
    message.success("已使用已有视频，未重复上传");
    invalidateVideoData();
  };

  const retryProcessing = useMutation({
    mutationFn: (assetId: string) => postJson("/api/admin/media/assets/" + assetId + "/retry-processing", {}),
    onSuccess: () => {
      message.success("已重新排队处理");
      invalidateVideoData();
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const duplicateDecision = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "kept" | "reused" | "ignored" }) =>
      patchJson("/api/admin/media/duplicate-candidates/" + id, { status }),
    onSuccess: () => {
      message.success("重复提示已更新");
      invalidateVideoData();
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const uploadBusy = batchRunning || ["hashing", "uploading", "paused", "finalizing"].includes(uploadState.stage);
  const canStartUpload = uploadItems.length > 0 && !batchRunning && uploadItems.some((item) => ["pending", "ready", "error"].includes(item.status)) && (uploadItems.length > 1 || Boolean(uploadItems[0].title.trim()));
  const canPause = Boolean(tusEndpoint && uppyRef.current && uppyFileIdRef.current && ["uploading", "paused"].includes(uploadState.stage));
  const canCancel = batchRunning || ["uploading", "paused", "finalizing", "hashing"].includes(uploadState.stage);
  const uploadFinished = uploadState.stage === "complete";
  const closeUploadModal = () => {
    resetUploadModal();
    setUploadOpen(false);
  };
  const uploadModalFooter = uploadFinished
    ? [
        <Button key="again" onClick={resetUploadModal}>继续上传其他视频</Button>,
        <Button key="done" type="primary" icon={<CheckCircleOutlined />} onClick={closeUploadModal}>完成并查看列表</Button>,
      ]
    : [
        <Button key="close" onClick={closeUploadModal}>关闭</Button>,
        canPause ? <Button key="pause" icon={uploadState.stage === "paused" ? <PlayCircleOutlined /> : <PauseCircleOutlined />} onClick={toggleUploadPause}>{uploadState.stage === "paused" ? "继续当前文件" : "暂停当前文件"}</Button> : null,
        uploadState.stage === "error" && !batchRunning ? <Button key="retry" icon={<ReloadOutlined />} onClick={retryUpload}>重试队列</Button> : null,
        canCancel ? <Button key="cancel" danger icon={<CloseCircleOutlined />} onClick={cancelUpload}>取消队列</Button> : null,
        <Button key="upload" type="primary" icon={<CloudUploadOutlined />} loading={uploadBusy && uploadState.stage !== "paused"} disabled={!canStartUpload} onClick={() => void startUpload()}>{uploadItems.length > 1 ? "开始队列上传" : tusEndpoint ? "开始上传" : "小文件上传"}</Button>,
      ].filter(Boolean);

  const renderAssetBadges = (asset: MediaAsset) => (
    <Space size={[4, 4]} wrap className="video-asset-badges">
      {hasPendingDuplicate(asset) ? <Tag color="#b8892f">疑似重复待确认</Tag> : null}
      {asset.upload_status !== "ready" && asset.upload_status !== "failed" ? <Tag>{processingPhaseText(asset)}</Tag> : null}
    </Space>
  );

  const renderAssetName = (asset: MediaAsset) => (
    <Space size={10} align="start" className="video-asset-name">
      <MediaThumbnail asset={asset} compact />
      <Space direction="vertical" size={1}>
        <Text strong>{asset.title}</Text>
        <Text type="secondary">{asset.original_file_name}</Text>
        {renderAssetBadges(asset)}
      </Space>
    </Space>
  );

  const renderProcessingLine = (asset: MediaAsset) => {
    if (asset.upload_status === "ready") return <Text type="secondary">{formatDurationSeconds(asset.duration_seconds)} · {formatResolution(asset)}</Text>;
    if (asset.upload_status === "failed") return <Text type="danger">{asset.error_reason || asset.processing_job?.error_reason || "处理失败"}</Text>;
    return <Progress percent={processingProgressValue(asset)} size="small" status="active" format={() => processingPhaseText(asset)} />;
  };

  const renderVersionPanel = (asset: MediaAsset) => {
    const { rendition, savedPercent } = renditionSavings(asset);
    return (
      <div className="video-version-panel">
        <div className="video-version-item">
          <Text strong>原始文件</Text>
          <Text type="secondary" className="block-text">老师上传的源文件，保留在本地媒体目录，用于备份、审计和后续重新处理。</Text>
          <Text>{formatBytes(asset.file_size_bytes)} · {formatResolution(asset)} · {(asset.video_codec || "-") + " / " + (asset.audio_codec || "-")}</Text>
        </div>
        <div className="video-version-item">
          <Text strong>学生播放源</Text>
          <Text type="secondary" className="block-text">后台用 FFmpeg 生成或确认的学生观看文件；这里会显示体积、分辨率和节省比例。</Text>
          <Text>{rendition ? formatBytes(rendition.file_size_bytes) + " · " + formatResolution(rendition) + (savedPercent ? " · 节省 " + savedPercent + "%" : " · 未明显压缩") : "未生成或仍在处理中"}</Text>
        </div>
      </div>
    );
  };

  const renderDuplicateCandidates = (asset: MediaAsset) => {
    const candidates = asset.duplicate_candidates || [];
    if (!candidates.length) return null;
    return (
      <div className="video-duplicate-panel">
        <Flex justify="space-between" align="start" gap={12} wrap="wrap">
          <div>
            <Text strong>疑似内容重复</Text>
            <Text type="secondary" className="block-text">这是 vPDQ/ThreatExchange 相似度工具给出的内容相近提示，不代表 SHA-256 完全相同；系统不会自动删除或跳过。</Text>
          </div>
          <Tag color={hasPendingDuplicate(asset) ? "#b8892f" : "default"}>{pendingDuplicateCandidates(asset).length ? pendingDuplicateCandidates(asset).length + " 个待确认" : "已处理"}</Tag>
        </Flex>
        <div className="video-duplicate-list">
          {candidates.map((candidate) => (
            <div key={candidate.id} className="video-duplicate-item">
              <Space align="center" size={10} className="video-duplicate-copy">
                <div className="video-duplicate-thumb">
                  <AuthenticatedImage
                    src={candidate.candidate_asset_id ? apiBase + "/api/admin/media/assets/" + candidate.candidate_asset_id + "/thumbnail" : null}
                    alt={candidate.candidate_title || "疑似重复视频"}
                    className="video-thumb-image compact"
                  />
                  <VideoCameraOutlined />
                </div>
                <div>
                  <Text strong>{candidate.candidate_title || candidate.candidate_asset_id || "未知视频"}</Text>
                  <Text type="secondary" className="block-text">
                    内容相似度 {duplicateScoreText(candidate.score)} · {candidate.algorithm} · {duplicateDecisionLabels[candidate.status] || candidate.status}
                  </Text>
                </div>
              </Space>
              <div className="video-duplicate-actions">
                {candidate.status === "pending" ? (
                  <Space size={6} wrap>
                    <Button size="small" onClick={() => duplicateDecision.mutate({ id: candidate.id, status: "kept" })}>保留两个</Button>
                    <Button size="small" onClick={() => duplicateDecision.mutate({ id: candidate.id, status: "reused" })}>复用已有</Button>
                    <Button size="small" onClick={() => duplicateDecision.mutate({ id: candidate.id, status: "ignored" })}>忽略提示</Button>
                  </Space>
                ) : (
                  <Tag>{duplicateDecisionLabels[candidate.status] || candidate.status}</Tag>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="视频资源"
        description="这里是后台的视频资源库，用来集中管理老师上传的视频文件。上传支持断点续传，上传完成后系统会在后台自动读取视频信息、生成真实缩略图、为学生端选择或生成更适合在线播放的学生播放源，并提示可能重复的视频。这个页面只负责上传、检索、预览和处理状态查看；把视频引用到具体实验点，仍然在实验管理页面完成。若出现处理失败，通常表示后台无法读取或生成视频输出，比如文件损坏、编码不兼容、磁盘空间不足或视频处理服务中断，可以稍后重试。"
        extra={<Button type="primary" icon={<CloudUploadOutlined />} onClick={() => setUploadOpen(true)}>上传视频</Button>}
      />

      <div className="video-resource-metrics">
        <Card><Statistic title="资源库视频" value={assets.data?.total || 0} prefix={<VideoCameraOutlined />} /></Card>
        <Card><Statistic title="可预览" value={readyAssets.length} /></Card>
        <Card><Statistic title="处理中" value={workingAssets.length} /></Card>
        <Card><Statistic title="待确认重复" value={pendingDuplicateAssets.length} /></Card>
        <Card><Statistic title="处理失败" value={failedAssets.length} /></Card>
        <Card><Statistic title="原始空间" value={formatBytes(sourceBytes)} /></Card>
        <Card><Statistic title="学生播放源空间" value={formatBytes(renditionBytes)} /></Card>
        <Card><Statistic title="已节省空间" value={savedBytes ? formatBytes(savedBytes) : "-"} suffix={savedPercent ? " / " + savedPercent + "%" : undefined} /></Card>
      </div>

      <div className="video-drive-panel">
        {pendingDuplicateAssets.length ? (
          <Alert
            type="warning"
            showIcon
            className="video-review-alert"
            message={"有 " + pendingDuplicateAssets.length + " 个疑似重复视频待确认"}
            description="这些视频内容可能与已有视频相近，但不是完全相同文件。建议集中查看后决定保留、复用已有视频或忽略提示。"
            action={<Button size="small" onClick={() => setStatusFilter("duplicate_pending")}>查看待确认</Button>}
          />
        ) : null}
        <Flex justify="space-between" align="center" gap={14} wrap="wrap" className="video-drive-toolbar">
          <Input.Search allowClear placeholder="搜索视频标题或文件名" value={keyword} onChange={(event) => setKeyword(event.target.value)} style={{ width: 360 }} />
          <Space size={10} wrap>
            <Select allowClear placeholder="全部状态" value={statusFilter} onChange={setStatusFilter} style={{ width: 160 }} options={[{ value: "duplicate_pending", label: "待确认重复" }, { value: "ready", label: "就绪" }, { value: "processing", label: "处理中" }, { value: "pending", label: "待处理" }, { value: "failed", label: "处理失败" }, { value: "replaced", label: "已替换" }]} />
            <Select value={sortKey} onChange={setSortKey} style={{ width: 150 }} options={[{ value: "updated_desc", label: "最近更新" }, { value: "name_asc", label: "名称 A-Z" }, { value: "size_desc", label: "文件最大" }]} />
            <Segmented value={viewMode} onChange={(value) => setViewMode(value as "grid" | "list")} options={[{ value: "list", icon: <UnorderedListOutlined />, label: "条" }, { value: "grid", icon: <AppstoreOutlined />, label: "块" }]} />
          </Space>
        </Flex>

        <QueryState loading={assets.isLoading} error={assets.error} empty={!assetItems.length}>
          {!filteredAssets.length ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有匹配的视频" /> : viewMode === "grid" ? (
            <div className="video-drive-grid">
              {filteredAssets.map((asset) => (
                <div className="video-asset-card" key={asset.id}>
                  <button type="button" className="video-asset-cover" onClick={() => setPreviewAsset(asset)} disabled={!isPreviewableVideo(asset)}><MediaThumbnail asset={asset} /></button>
                  <Space direction="vertical" size={8} className="full">
                    <div><Text strong className="video-asset-title">{asset.title}</Text><Text type="secondary" className="video-asset-file">{asset.original_file_name}</Text></div>
                    <Flex justify="space-between" align="center" gap={8}>{mediaStatusTag(asset.upload_status)}<Text type="secondary">{formatBytes(asset.file_size_bytes)}</Text></Flex>
                    {renderProcessingLine(asset)}
                    {renderAssetBadges(asset)}
                    <Flex justify="space-between" align="center" gap={8}>
                      <Text type="secondary">{mediaAssetTime(asset)}</Text>
                      <Space size={6}>{asset.upload_status === "failed" ? <Button size="small" icon={<ReloadOutlined />} loading={retryProcessing.isPending} onClick={() => retryProcessing.mutate(asset.id)}>重试</Button> : null}<Button size="small" icon={<EyeOutlined />} disabled={!isPreviewableVideo(asset)} onClick={() => setPreviewAsset(asset)}>预览</Button></Space>
                    </Flex>
                  </Space>
                </div>
              ))}
            </div>
          ) : (
            <Table rowKey="id" dataSource={filteredAssets} pagination={{ pageSize: 12, showSizeChanger: false }} columns={[{ title: "文件名", render: (_: unknown, asset: MediaAsset) => renderAssetName(asset) }, { title: "处理", width: 190, render: (_: unknown, asset: MediaAsset) => renderProcessingLine(asset) }, { title: "大小", width: 110, render: (_: unknown, asset: MediaAsset) => formatBytes(asset.file_size_bytes) }, { title: "状态", width: 110, render: (_: unknown, asset: MediaAsset) => mediaStatusTag(asset.upload_status) }, { title: "引用", width: 90, render: (_: unknown, asset: MediaAsset) => asset.association_count || 0 }, { title: "更新时间", width: 170, render: (_: unknown, asset: MediaAsset) => mediaAssetTime(asset) }, { title: "操作", width: 170, render: (_: unknown, asset: MediaAsset) => <Space size={6}>{asset.upload_status === "failed" ? <Button size="small" icon={<ReloadOutlined />} onClick={() => retryProcessing.mutate(asset.id)}>重试</Button> : null}<Button size="small" icon={<EyeOutlined />} disabled={!isPreviewableVideo(asset)} onClick={() => setPreviewAsset(asset)}>预览</Button></Space> }]} />
          )}
        </QueryState>
      </div>

      <Modal title="上传视频" open={uploadOpen} onCancel={closeUploadModal} footer={uploadModalFooter} width={780}>
        <Space direction="vertical" size={14} className="full">
          {!uploadFinished ? (
            <>
              {!tusEndpoint ? <Alert type="warning" showIcon message="当前使用小文件回退上传" description="配置 VITE_TUS_ENDPOINT 后可启用断点续传。" /> : null}
              <Input
                placeholder={uploadItems.length > 1 ? "多个视频将默认使用各自文件名作为标题" : "视频标题"}
                value={uploadItems.length > 1 ? "" : uploadTitle}
                disabled={uploadItems.length > 1 || batchRunning}
                onChange={(event) => updateSingleUploadTitle(event.target.value)}
              />
              <div className="video-upload-guide">
                <div className="video-upload-guide-head">
                  <div>
                    <Text strong>上传后会自动处理</Text>
                    <Text type="secondary" className="block-text">{uploadStageText(uploadState.stage)}</Text>
                  </div>
                  <span>{tusEndpoint ? "断点续传" : "小文件上传"}</span>
                </div>
                <div className="video-upload-flow">
                  {[
                    {
                      title: "校验",
                      description: uploadState.stage === "hashing" ? "正在校验 " + uploadState.hashProgress + "%" : "识别完全重复文件",
                    },
                    {
                      title: "上传",
                      description: tusEndpoint ? "中断后可继续传" : "当前走普通上传",
                    },
                    {
                      title: "处理",
                      description: "缩略图、学生播放源、相似度",
                    },
                  ].map((step, index) => {
                    const currentStep = uploadStepCurrent(uploadState.stage);
                    const stateClass = currentStep > index ? "done" : currentStep === index ? "active" : "";
                    return (
                      <div key={step.title} className={`video-upload-flow-step ${stateClass}`}>
                        <span className="video-upload-flow-dot">{currentStep > index ? <CheckCircleOutlined /> : index + 1}</span>
                        <div>
                          <strong>{step.title}</strong>
                          <small>{step.description}</small>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="video-upload-guide-notes">
                  <span>同一浏览器重新选择同一文件，会尽量从已上传位置继续</span>
                  <span>多个视频会按队列串行上传，完成后进入后台处理</span>
                </div>
              </div>
              <Upload.Dragger
                accept="video/*,.mp4,.mov,.m4v,.webm,.avi"
                multiple
                showUploadList={false}
                disabled={batchRunning}
                beforeUpload={(file, fileList) => {
                  const maybeFile = file as File & { uid?: string };
                  const lastFile = fileList[fileList.length - 1] as File & { uid?: string };
                  if (maybeFile.uid === lastFile?.uid) handleUploadFiles(fileList as File[]);
                  return false;
                }}
              >
                <p className="ant-upload-drag-icon"><CloudUploadOutlined /></p>
                <p className="ant-upload-text">拖拽一个或多个视频到这里，或点击选择文件</p>
                <p className="ant-upload-hint">支持 mp4、mov、m4v、webm、avi；多个文件会串行上传，上传完成后自动进入后台处理。</p>
              </Upload.Dragger>
            </>
          ) : (
            <div className="video-upload-complete-card">
              <span className="video-upload-complete-icon"><CheckCircleOutlined /></span>
              <div>
                <Text strong>上传已完成，视频已加入后台处理队列</Text>
                <Text type="secondary" className="block-text">现在可以回到列表查看结果。后台会继续读取元数据、生成真实缩略图、准备学生播放源，并完成相似视频检测；列表会自动刷新处理阶段。</Text>
              </div>
            </div>
          )}
          {uploadItems.length ? (
            <div className="video-upload-queue">
              <Flex justify="space-between" align="center" gap={10} wrap="wrap">
                <Text strong>{batchRunning ? "队列上传中" : "上传队列"}</Text>
                <Text type="secondary">{uploadQueueDoneCount} / {uploadItems.length} 个已处理 · {formatBytes(uploadQueueUploadedBytes)} / {formatBytes(uploadQueueTotalBytes)}</Text>
              </Flex>
              <Progress percent={uploadQueueProgress} status={uploadState.stage === "error" ? "exception" : batchRunning ? "active" : "normal"} />
              <div className="video-upload-queue-list">
                {uploadItems.map((item, index) => {
                  const itemPercent = item.status === "hashing" ? item.hashProgress : item.progress;
                  const itemActive = item.id === currentUploadId;
                  return (
                    <div key={item.id} className={itemActive ? "video-upload-queue-item active" : "video-upload-queue-item"}>
                      <div className="video-upload-queue-copy">
                        <Text strong>{index + 1}. {item.title || videoTitleFromFile(item.file)}</Text>
                        <Text type="secondary" className="block-text">{item.file.name} · {formatBytes(item.file.size)}</Text>
                        {item.duplicateAsset ? <Text type="secondary" className="block-text">复用：{item.duplicateAsset.title}</Text> : null}
                      </div>
                      <div className="video-upload-queue-state">
                        <Tag color={item.status === "error" ? "red" : ["duplicate", "processing", "complete"].includes(item.status) ? "green" : itemActive ? "#b8892f" : "default"}>{uploadQueueItemText(item)}</Tag>
                        {["hashing", "uploading", "paused", "finalizing"].includes(item.status) ? <Progress percent={itemPercent} size="small" status={item.status === "paused" ? "normal" : "active"} /> : null}
                      </div>
                      {!batchRunning && !uploadFinished ? (
                        <Button
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => {
                            const nextItems = uploadItems.filter((candidate) => candidate.id !== item.id);
                            uploadItemsRef.current = nextItems;
                            setUploadItems(nextItems);
                            if (!nextItems.length) {
                              setUploadTitle("");
                              setUploadState(emptyUploadState);
                              return;
                            }
                            if (nextItems.length === 1) setUploadTitle(nextItems[0].title);
                            setUploadState((current) => ({
                              ...current,
                              stage: nextItems.length ? current.stage : "idle",
                              uploadedBytes: nextItems.reduce((sum, candidate) => sum + candidate.uploadedBytes, 0),
                              totalBytes: nextItems.reduce((sum, candidate) => sum + candidate.totalBytes, 0),
                              note: nextItems.length > 1 ? `已选择 ${nextItems.length} 个视频，将按顺序逐个上传。` : undefined,
                            }));
                          }}
                        >
                          移除
                        </Button>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
          {uploadState.stage === "hashing" ? <div className="video-upload-status"><Text strong>正在校验当前文件</Text><Progress percent={uploadState.hashProgress} /></div> : null}
          {uploadState.note && !["processing", "complete"].includes(uploadState.stage) ? <div className="video-upload-inline-note">{uploadState.note}</div> : null}
          {(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset) ? <Alert type="success" showIcon message="发现完全相同的已上传文件" description={<Space align="center" size={12}><MediaThumbnail asset={(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset) as MediaAsset} compact /><div><Text strong>{(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.title}</Text><Text type="secondary" className="block-text">{(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.original_file_name} · {formatBytes((currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.file_size_bytes)} · {mediaStatusLabels[(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.upload_status || ""] || (currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.upload_status}</Text></div></Space>} /> : null}
          {["uploading", "paused", "finalizing"].includes(uploadState.stage) ? <div className="video-upload-status"><Flex justify="space-between" align="center"><Text strong>{uploadState.stage === "finalizing" ? "正在完成当前文件入库" : uploadState.stage === "paused" ? "当前文件已暂停" : "正在上传当前文件"}</Text><Text type="secondary">{formatBytes(uploadState.uploadedBytes)} / {formatBytes(uploadState.totalBytes || currentUploadItem?.file.size)}</Text></Flex><Progress percent={uploadState.progress} status={uploadState.stage === "paused" ? "normal" : "active"} /></div> : null}
          {uploadState.stage === "processing" ? (
            <div className="video-upload-inline-note success">当前文件已上传，队列会继续上传后续文件；已完成的视频会留在列表里显示后台处理阶段。</div>
          ) : null}
          {uploadState.error ? <Alert type="error" showIcon message={uploadState.error} /> : null}
        </Space>
      </Modal>

      <Modal
        title={previewAsset ? (
          <Space size={8} wrap className="video-preview-title">
            <span>{previewAsset.title}</span>
            {hasPendingDuplicate(previewAsset) ? <Tag color="#b8892f">疑似重复待确认</Tag> : null}
          </Space>
        ) : "视频预览"}
        open={Boolean(previewAsset)}
        onCancel={() => setPreviewAsset(null)}
        footer={[<Button key="close" onClick={() => setPreviewAsset(null)}>关闭</Button>]}
        width={1040}
      >
        {previewAsset ? (
          <Space direction="vertical" size={16} className="full">
            {hasPendingDuplicate(previewAsset) ? (
              <Alert
                type="warning"
                showIcon
                message="这个视频可能与已有视频内容相近"
                description="这是感知相似度检测结果，不是完全相同文件。请在下方重复审核区确认保留、复用或忽略。"
              />
            ) : null}
            <div className="video-preview-layout">
              <div className="video-preview-stage">
                {previewLoading ? <Spin /> : previewError ? <Alert type="error" showIcon message={previewError} /> : previewUrl ? <video controls preload="metadata" className="video-preview-player" src={previewUrl} poster={previewPosterUrl} /> : <Alert type="info" showIcon message="该视频当前不可预览" description="只有上传状态为就绪的视频可以在线播放。" />}
              </div>
              <Descriptions
                size="small"
                column={1}
                items={[
                  { key: "file", label: "原始文件", children: previewAsset.original_file_name },
                  { key: "status", label: "状态", children: mediaStatusTag(previewAsset.upload_status) },
                  { key: "phase", label: "处理阶段", children: processingPhaseText(previewAsset) },
                  { key: "source", label: "原始大小", children: formatBytes(previewAsset.file_size_bytes) },
                  { key: "duration", label: "时长", children: formatDurationSeconds(previewAsset.duration_seconds) },
                  { key: "resolution", label: "分辨率", children: formatResolution(previewAsset) },
                  { key: "codec", label: "编码", children: (previewAsset.video_codec || "-") + " / " + (previewAsset.audio_codec || "-") },
                  { key: "rendition", label: "学生播放源", children: selectedRendition(previewAsset) ? formatBytes(selectedRendition(previewAsset)?.file_size_bytes) + " · " + formatResolution(selectedRendition(previewAsset)) : "未生成" },
                  { key: "playback", label: "播放源", children: previewAsset.playback_relative_path ? "学生播放源（预览/学生端优先使用）" : "原始文件（原文件已可播放）" },
                  { key: "time", label: "更新时间", children: mediaAssetTime(previewAsset) },
                ]}
              />
            </div>
            {renderVersionPanel(previewAsset)}
            {previewAsset.upload_status !== "ready" ? <Progress percent={processingProgressValue(previewAsset)} status={previewAsset.upload_status === "failed" ? "exception" : "active"} format={() => processingPhaseText(previewAsset)} /> : null}
            {previewAsset.error_reason ? <Alert type="error" showIcon message={previewAsset.error_reason} /> : null}
            {renderDuplicateCandidates(previewAsset)}
          </Space>
        ) : null}
      </Modal>
    </Space>
  );
}
