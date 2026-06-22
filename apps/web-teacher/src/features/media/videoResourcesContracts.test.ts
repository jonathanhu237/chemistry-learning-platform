import { describe, expect, it } from "vitest";
import mediaApiSource from "../../api/media.ts?raw";
import videoResourcesSource from "./VideoResourcesPage.tsx?raw";

describe("video resource lifecycle contracts", () => {
  it("archives stored assets through media lifecycle APIs without catalog binding calls", () => {
    expect(mediaApiSource).toContain("type MediaAssetArchivePlan");
    expect(mediaApiSource).toContain("type MediaAssetArchiveResult");
    expect(mediaApiSource).toContain("getMediaAssetArchivePlan");
    expect(mediaApiSource).toContain('"/api/admin/media/assets/" + assetId + "/archive-plan"');
    expect(mediaApiSource).toContain('"/api/admin/media/assets/" + assetId + "/archive"');

    expect(videoResourcesSource).toContain("getMediaAssetArchivePlan(asset.id)");
    expect(videoResourcesSource).toContain("archiveMediaAsset(assetId, reason)");
    expect(videoResourcesSource).toContain('reason: "teacher_video_resource_archive"');
    expect(videoResourcesSource).toContain("catalog_binding_count");
    expect(videoResourcesSource).toContain("catalog_bindings");
    expect(videoResourcesSource).toContain("student_visible_catalog_binding_count");
    expect(videoResourcesSource).toContain("renderAssetActions(asset)");
    expect(videoResourcesSource).toContain("confirmArchiveAsset(asset)");
    expect(videoResourcesSource).toContain("setPreviewAsset(null)");
    expect(videoResourcesSource).toContain('queryKey: ["media-assets"]');
    expect(videoResourcesSource).not.toContain("/api/admin/catalog");
    expect(videoResourcesSource).not.toContain("setMediaBindingStatus");
    expect(videoResourcesSource).not.toContain("deleteMediaBinding");
  });

  it("keeps pending upload queue removal separate from stored asset archive", () => {
    expect(videoResourcesSource).toContain("uploadItems.filter((candidate) => candidate.id !== item.id)");
    expect(videoResourcesSource).toContain("setUploadItems(nextItems)");
    expect(videoResourcesSource).toContain("archiveAsset = useMutation");
    expect(videoResourcesSource).toContain("renderAssetActions(asset)");
    expect(videoResourcesSource).toContain("asset.lifecycle_status === \"archived\"");
    expect(videoResourcesSource).toContain("<DeleteOutlined />");
    expect(videoResourcesSource).not.toContain("archiveMediaAsset(item.id");
    expect(videoResourcesSource).not.toContain("getMediaAssetArchivePlan(item.id");
  });

  it("requires archive impact confirmation copy before removing bound point videos", () => {
    expect(videoResourcesSource).toContain("modal.confirm");
    expect(videoResourcesSource).toContain("catalog_binding_count ? \"warning\" : \"info\"");
    expect(videoResourcesSource).toContain("point_title || item.placement_node_id");
    expect(videoResourcesSource).toContain('(item.catalog_path || []).join(" / ")');
    expect(videoResourcesSource).toContain("active_processing_job_count");
    expect(videoResourcesSource).toContain("archived_binding_count");
    expect(videoResourcesSource).toContain("\u70b9\u4f4d\u6587\u5b57\u5185\u5bb9\u3001\u9898\u76ee\u3001\u53d1\u5e03\u72b6\u6001\u4e0d\u4f1a\u88ab\u5220\u9664");
    expect(videoResourcesSource).toContain("\u5c06\u79fb\u9664 ${plan.catalog_binding_count} \u4e2a\u70b9\u4f4d\u89c6\u9891\u7ed1\u5b9a");
    expect(videoResourcesSource).not.toContain("mutations.bindMedia");
  });
});
