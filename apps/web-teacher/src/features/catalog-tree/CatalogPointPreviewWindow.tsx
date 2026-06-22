import { useMemo, useState } from "react";
import { Button, Empty, Select, Space, Typography } from "antd";
import { ExportOutlined, ReloadOutlined } from "@ant-design/icons";
import { useSearchParams } from "react-router-dom";

import {
  DeviceFrame,
  devicePresets,
  openDevicePreviewWindow,
  resolveStudentPreviewUrl,
  type DevicePreset,
} from "../device-preview/DevicePreviewFrame";
import "./catalogTree.css";

const { Text, Title } = Typography;

function formatExpiry(value: string): string {
  if (!value) return "本次预览链接短时有效";
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return value;
  return `有效至 ${new Date(timestamp).toLocaleString()}`;
}

export function CatalogPointPreviewWindow() {
  const [searchParams] = useSearchParams();
  const [deviceKey, setDeviceKey] = useState<DevicePreset["key"]>("iphone17Pro");
  const previewUrl = searchParams.get("previewUrl") || "";
  const title = searchParams.get("title") || "学习卡片预览";
  const expiresAt = searchParams.get("expiresAt") || "";
  const iframeSrc = useMemo(() => resolveStudentPreviewUrl(previewUrl), [previewUrl]);
  const preset = devicePresets.find((item) => item.key === deviceKey) || devicePresets[0];

  if (!iframeSrc) {
    return (
      <div className="catalog-preview-window">
        <Empty description="缺少预览链接，请从点位工作台重新打开预览。" />
      </div>
    );
  }

  return (
    <div className="catalog-preview-window">
      <header className="catalog-preview-toolbar">
        <div>
          <Title level={4}>{title}</Title>
          <Text type="secondary">{formatExpiry(expiresAt)}</Text>
        </div>
        <Space wrap>
          <Select
            aria-label="选择预览设备"
            className="catalog-preview-device-select"
            value={deviceKey}
            options={devicePresets.map((item) => ({ value: item.key, label: item.label }))}
            onChange={(value) => setDeviceKey(value as DevicePreset["key"])}
          />
          <Button icon={<ReloadOutlined />} onClick={() => window.location.reload()}>
            刷新
          </Button>
          <Button
            className="catalog-preview-page-button"
            icon={<ExportOutlined />}
            onClick={() => openDevicePreviewWindow(iframeSrc, preset)}
          >
            页面预览
          </Button>
        </Space>
      </header>
      <main className="catalog-preview-stage">
        <DeviceFrame preset={preset}>
          <iframe className="catalog-preview-iframe" title={`预览 ${title}`} src={iframeSrc} />
        </DeviceFrame>
      </main>
    </div>
  );
}
