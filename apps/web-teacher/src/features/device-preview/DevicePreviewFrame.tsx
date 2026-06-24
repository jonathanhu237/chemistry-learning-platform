import type { ReactNode } from "react";
import { AndroidMockup, IPhoneMockup } from "react-device-mockup";

export type DevicePreset =
  | {
      key: "iphone17Pro" | "iphone17" | "iphone17ProMax" | "iphone15" | "iphone14" | "iphoneSE";
      label: string;
      family: "iphone";
      screenWidth: number;
      viewportHeight: number;
      screenType: "legacy" | "notch" | "island";
    }
  | {
      key:
        | "huaweiMate80Pro"
        | "huaweiPura80Pro"
        | "xiaomi17"
        | "xiaomi17Ultra"
        | "oppoFindX8Pro"
        | "vivoX200Pro"
        | "android";
      label: string;
      family: "android";
      screenWidth: number;
      viewportHeight: number;
      camera: "center-hole" | "left-hole" | "pill" | "wide-pill" | "fold-inner";
      cameraLabel: string;
    };

export const devicePresets: DevicePreset[] = [
  { key: "iphone17Pro", label: "iPhone 17 Pro", family: "iphone", screenWidth: 402, viewportHeight: 874, screenType: "island" },
  { key: "iphone17", label: "iPhone 17", family: "iphone", screenWidth: 402, viewportHeight: 874, screenType: "island" },
  { key: "iphone17ProMax", label: "iPhone 17 Pro Max", family: "iphone", screenWidth: 440, viewportHeight: 956, screenType: "island" },
  { key: "iphone15", label: "iPhone 15 Pro", family: "iphone", screenWidth: 393, viewportHeight: 852, screenType: "island" },
  { key: "iphone14", label: "iPhone 14", family: "iphone", screenWidth: 390, viewportHeight: 844, screenType: "notch" },
  { key: "iphoneSE", label: "iPhone SE", family: "iphone", screenWidth: 375, viewportHeight: 667, screenType: "legacy" },
  {
    key: "huaweiMate80Pro",
    label: "HUAWEI Mate 80 Pro",
    family: "android",
    screenWidth: 427,
    viewportHeight: 945,
    camera: "pill",
    cameraLabel: "pill camera",
  },
  {
    key: "huaweiPura80Pro",
    label: "HUAWEI Pura 80 Pro",
    family: "android",
    screenWidth: 425,
    viewportHeight: 949,
    camera: "wide-pill",
    cameraLabel: "wide pill camera",
  },
  {
    key: "xiaomi17",
    label: "Xiaomi 17",
    family: "android",
    screenWidth: 407,
    viewportHeight: 885,
    camera: "center-hole",
    cameraLabel: "center punch-hole",
  },
  {
    key: "xiaomi17Ultra",
    label: "Xiaomi 17 Ultra",
    family: "android",
    screenWidth: 400,
    viewportHeight: 869,
    camera: "center-hole",
    cameraLabel: "center punch-hole",
  },
  {
    key: "oppoFindX8Pro",
    label: "OPPO Find X8 Pro",
    family: "android",
    screenWidth: 421,
    viewportHeight: 927,
    camera: "left-hole",
    cameraLabel: "left punch-hole",
  },
  {
    key: "vivoX200Pro",
    label: "vivo X200 Pro",
    family: "android",
    screenWidth: 420,
    viewportHeight: 933,
    camera: "center-hole",
    cameraLabel: "center punch-hole",
  },
  {
    key: "android",
    label: "Android Generic",
    family: "android",
    screenWidth: 412,
    viewportHeight: 892,
    camera: "fold-inner",
    cameraLabel: "inner-screen camera",
  },
];

const defaultStudentPreviewAppBase = "http://222.200.189.249:15173";

export function inferStudentAppBase(): string {
  const configured = String(import.meta.env.VITE_STUDENT_APP_BASE_URL || "").replace(/\/$/, "");
  if (configured) return configured;
  return defaultStudentPreviewAppBase;
}

export function resolveStudentPreviewUrl(previewUrl: string): string {
  if (!previewUrl) return "";
  try {
    return new URL(previewUrl).toString();
  } catch {
    return new URL(previewUrl, inferStudentAppBase()).toString();
  }
}

export function openDevicePreviewWindow(url: string, preset: DevicePreset) {
  const width = Math.min(Math.max(preset.screenWidth + 28, 390), 540);
  const height = Math.min(Math.max(preset.viewportHeight + 112, 720), 1080);
  const popup = window.open(url, "_blank", `popup,width=${width},height=${height}`);
  if (!popup) return;
  popup.opener = null;
  popup.focus();
}

export function DeviceFrame({
  preset,
  children,
  hideHardwareButtons = false,
}: {
  preset: DevicePreset;
  children: ReactNode;
  hideHardwareButtons?: boolean;
}) {
  if (preset.family === "android") {
    return (
      <div className="device-preview-android-shell catalog-preview-android-shell">
        <AndroidMockup
          screenWidth={preset.screenWidth}
          frameColor="#1f2933"
          statusbarColor="#f7faf9"
          navBarColor="#f7faf9"
          frameOnly={hideHardwareButtons}
          className="device-preview-device catalog-preview-device"
        >
          {children}
        </AndroidMockup>
        <span className="device-preview-camera-note catalog-preview-camera-note">{preset.cameraLabel}</span>
      </div>
    );
  }
  return (
    <IPhoneMockup
      screenWidth={preset.screenWidth}
      screenType={preset.screenType}
      frameColor="#1f2933"
      statusbarColor="#f7faf9"
      frameOnly={hideHardwareButtons}
      className="device-preview-device catalog-preview-device"
    >
      {children}
    </IPhoneMockup>
  );
}
