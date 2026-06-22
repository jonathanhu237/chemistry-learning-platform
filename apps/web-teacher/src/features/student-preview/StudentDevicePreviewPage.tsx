import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { Alert, Button, Segmented, Select, Slider, Space, Spin, Typography } from "antd";
import { ExportOutlined, MobileOutlined, ReloadOutlined, SyncOutlined } from "@ant-design/icons";
import { useMutation } from "@tanstack/react-query";

import {
  DeviceFrame,
  devicePresets,
  inferStudentAppBase,
  openDevicePreviewWindow,
  resolveStudentPreviewUrl,
  type DevicePreset,
} from "../device-preview/DevicePreviewFrame";
import { createStudentPreviewSession, type TeacherStudentPreviewSession } from "./studentPreviewApi";
import { PreviewGestureSurface } from "./input/PreviewGestureSurface";
import { appendPreviewFrameId, createPreviewFrameId } from "./input/previewInputProtocol";

import "./studentPreview.css";

const { Text, Title } = Typography;

type Orientation = "portrait" | "landscape";

function formatExpiry(value?: string): string {
  if (!value) return "-";
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return value;
  return new Date(timestamp).toLocaleString();
}

function allowedPreviewUrl(value: string): string {
  const resolved = resolveStudentPreviewUrl(value);
  const expectedOrigin = new URL(inferStudentAppBase()).origin;
  const actualOrigin = new URL(resolved).origin;
  if (actualOrigin !== expectedOrigin) {
    throw new Error(`Preview origin ${actualOrigin} is not allowed. Expected ${expectedOrigin}.`);
  }
  return resolved;
}

export function StudentDevicePreviewPage() {
  const [deviceKey, setDeviceKey] = useState<DevicePreset["key"]>("iphone17Pro");
  const [orientation, setOrientation] = useState<Orientation>("portrait");
  const [zoom, setZoom] = useState(86);
  const [iframeKey, setIframeKey] = useState(0);
  const [iframeLoading, setIframeLoading] = useState(false);
  const [session, setSession] = useState<TeacherStudentPreviewSession | null>(null);
  const [frameId, setFrameId] = useState(() => createPreviewFrameId());
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  const preset = devicePresets.find((item) => item.key === deviceKey) || devicePresets[0];
  const previewUrl = useMemo(() => {
    if (!session?.preview_url) return { src: "", error: "" };
    try {
      return { src: appendPreviewFrameId(allowedPreviewUrl(session.preview_url), frameId), error: "" };
    } catch (error) {
      return { src: "", error: error instanceof Error ? error.message : "Preview URL is invalid." };
    }
  }, [frameId, session?.preview_url]);
  const iframeSrc = previewUrl.src;
  const urlError = previewUrl.error;
  const previewOrigin = iframeSrc ? new URL(iframeSrc).origin : "";

  const sessionMutation = useMutation({
    mutationFn: createStudentPreviewSession,
    onSuccess: (response) => {
      setSession(response);
      setFrameId(createPreviewFrameId());
      setIframeKey((value) => value + 1);
      setIframeLoading(true);
    },
  });

  useEffect(() => {
    sessionMutation.mutate();
  }, []);

  const openExternal = () => {
    if (!iframeSrc) return;
    openDevicePreviewWindow(iframeSrc, preset);
  };

  const refreshIframe = () => {
    if (!iframeSrc) return;
    setFrameId(createPreviewFrameId());
    setIframeLoading(true);
    setIframeKey((value) => value + 1);
  };

  return (
    <div className="student-preview-page">
      <header className="student-preview-header">
        <div>
          <Text className="eyebrow">学生预览</Text>
          <Title level={3}>学生预览</Title>
          <Text type="secondary">使用当前教师的隐藏测试学生账号，iframe 内运行真实 web-student。</Text>
        </div>
        <Space wrap>
          <Button icon={<SyncOutlined />} loading={sessionMutation.isPending} onClick={() => sessionMutation.mutate()}>
            重新生成会话
          </Button>
          <Button icon={<ReloadOutlined />} disabled={!iframeSrc} onClick={refreshIframe}>
            刷新 iframe
          </Button>
          <Button icon={<ExportOutlined />} disabled={!iframeSrc} onClick={openExternal}>
            独立窗口
          </Button>
        </Space>
      </header>

      <section className="student-preview-toolbar">
        <Select
          aria-label="选择设备"
          className="student-preview-device-select"
          value={deviceKey}
          options={devicePresets.map((item) => ({ value: item.key, label: item.label }))}
          onChange={(value) => setDeviceKey(value as DevicePreset["key"])}
        />
        <Segmented
          value={orientation}
          options={[
            { label: "竖屏", value: "portrait" },
            { label: "横屏", value: "landscape" },
          ]}
          onChange={(value) => setOrientation(value as Orientation)}
        />
        <div className="student-preview-zoom">
          <MobileOutlined />
          <Slider min={62} max={110} value={zoom} onChange={setZoom} tooltip={{ formatter: (value) => `${value}%` }} />
        </div>
        <Text type="secondary">会话有效期：{formatExpiry(session?.expires_at)}</Text>
      </section>

      {sessionMutation.isError ? (
        <Alert
          type="error"
          showIcon
          className="student-preview-alert"
          message="预览会话创建失败"
          description={sessionMutation.error instanceof Error ? sessionMutation.error.message : "请稍后重试。"}
        />
      ) : null}
      {urlError ? <Alert type="error" showIcon className="student-preview-alert" message="预览地址不在允许范围内" description={urlError} /> : null}

      <main
        className={`student-preview-stage ${orientation}`}
        style={{ "--student-preview-zoom": String(zoom / 100) } as CSSProperties}
      >
        {sessionMutation.isPending && !session ? (
          <div className="student-preview-loading">
            <Spin />
            <Text type="secondary">正在创建测试学生预览会话...</Text>
          </div>
        ) : iframeSrc ? (
          <>
            {iframeLoading ? (
              <div className="student-preview-frame-loading">
                <Spin />
              </div>
            ) : null}
            <div className="student-preview-frame-scale">
              <DeviceFrame preset={preset} hideHardwareButtons>
                <div className="student-preview-screen-bridge">
                <iframe
                  key={iframeKey}
                  ref={iframeRef}
                  className="student-preview-iframe"
                  title="学生端手机预览"
                  src={iframeSrc}
                  sandbox="allow-scripts allow-forms allow-same-origin allow-popups allow-downloads"
                  referrerPolicy="no-referrer"
                  onLoad={() => setIframeLoading(false)}
                />
                  <PreviewGestureSurface
                    enabled={Boolean(iframeSrc && previewOrigin && !iframeLoading)}
                    iframeRef={iframeRef}
                    frameId={frameId}
                    targetOrigin={previewOrigin}
                  />
                </div>
              </DeviceFrame>
            </div>
          </>
        ) : (
          <div className="student-preview-loading">
            <Text type="secondary">暂无可用预览会话。</Text>
          </div>
        )}
      </main>
    </div>
  );
}
