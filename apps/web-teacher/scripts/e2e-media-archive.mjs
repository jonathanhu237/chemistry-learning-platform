import { createHash, randomBytes } from "node:crypto";
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const repoRoot = new URL("../../../", import.meta.url);
const repoRootPath = fileURLToPath(repoRoot);

const baseUrl = process.env.E2E_BASE_URL || "http://localhost:5174";
const apiBaseUrl = process.env.E2E_API_BASE_URL || "http://localhost:8000";
const esUrl = (process.env.E2E_ES_URL || process.env.VIDEO_LIBRARY_SEARCH_URL || "http://127.0.0.1:9200").replace(/\/$/, "");
const esIndex = process.env.E2E_ES_INDEX || process.env.VIDEO_LIBRARY_SEARCH_INDEX || "student-video-library";
const runId = process.env.E2E_RUN_ID || randomBytes(6).toString("hex");
const username = process.env.E2E_ADMIN_USERNAME || "codex_media_archive_admin";
const password = process.env.E2E_ADMIN_PASSWORD || randomBytes(18).toString("base64url");
const shouldBootstrap = process.env.E2E_SKIP_BOOTSTRAP !== "1" && !process.env.E2E_ADMIN_PASSWORD;

function candidateChromePaths() {
  const paths = [];
  if (process.env.E2E_CHROME_PATH) {
    paths.push(process.env.E2E_CHROME_PATH);
  }
  if (process.platform === "win32") {
    const programFiles = process.env.ProgramFiles || "C:\\Program Files";
    const programFilesX86 = process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)";
    paths.push(
      `${programFiles}\\Google\\Chrome\\Application\\chrome.exe`,
      `${programFilesX86}\\Google\\Chrome\\Application\\chrome.exe`,
      `${programFiles}\\Microsoft\\Edge\\Application\\msedge.exe`,
      `${programFilesX86}\\Microsoft\\Edge\\Application\\msedge.exe`,
    );
  }
  return paths.filter((candidate) => candidate && existsSync(candidate));
}

async function requireHttpOk(url, name) {
  let response;
  try {
    response = await fetch(url);
  } catch (error) {
    throw new Error(`${name} is not reachable at ${url}: ${String(error)}`);
  }
  if (!response.ok) {
    throw new Error(`${name} returned HTTP ${response.status} at ${url}: ${await response.text()}`);
  }
}

function spawnOrThrow(command, args, options, failureIntro) {
  const result = spawnSync(command, args, {
    cwd: repoRootPath,
    encoding: "utf8",
    ...options,
  });
  if (result.status !== 0) {
    throw new Error(
      [
        failureIntro,
        `Command: ${command} ${args.join(" ")}`,
        result.stdout,
        result.stderr,
      ]
        .filter(Boolean)
        .join("\n"),
    );
  }
  return result;
}

function dockerPython(script, env = {}) {
  const envArgs = Object.entries(env).flatMap(([key, value]) => ["-e", `${key}=${value}`]);
  const result = spawnOrThrow(
    "docker",
    ["compose", "exec", "-T", "-e", "PYTHONPATH=/app", ...envArgs, "backend", "python", "-"],
    { input: script },
    "Unable to execute Python inside the backend Docker Compose service.",
  );
  const lines = result.stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const lastJson = [...lines].reverse().find((line) => line.startsWith("{") && line.endsWith("}"));
  if (!lastJson) {
    throw new Error(["Backend Python helper did not print a JSON result.", result.stdout, result.stderr].filter(Boolean).join("\n"));
  }
  return JSON.parse(lastJson);
}

function bootstrapAdmin() {
  if (!shouldBootstrap) {
    return { skipped: true, reason: process.env.E2E_ADMIN_PASSWORD ? "password provided" : "E2E_SKIP_BOOTSTRAP=1" };
  }
  spawnOrThrow(
    "docker",
    [
      "compose",
      "exec",
      "-T",
      "-e",
      "PYTHONPATH=/app",
      "backend",
      "python",
      "scripts/bootstrap_admin.py",
      "--skip-migrations",
      "--username",
      username,
      "--display-name",
      "Media Archive E2E Admin",
      "--role",
      "admin",
      "--password",
      password,
    ],
    {},
    "Unable to prepare local media archive admin through Docker Compose.",
  );
  return { skipped: false, username };
}

async function login() {
  const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error(`login failed with HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function api(path, token, options = {}) {
  const headers = { authorization: `Bearer ${token}`, ...(options.body === undefined ? {} : { "content-type": "application/json" }) };
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  if (!response.ok) {
    throw new Error(`${path} failed with HTTP ${response.status}: ${await response.text()}`);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function seedMediaAsset() {
  const script = String.raw`
from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings

run_id = os.environ["E2E_MEDIA_ARCHIVE_RUN_ID"]
username = os.environ["E2E_MEDIA_ARCHIVE_USERNAME"]
asset_id = str(uuid.uuid4())
title = f"E2E media archive resource {run_id}"
original_file_name = f"e2e-media-archive-{run_id}.mp4"
relative_path = f"e2e/media-archive/{original_file_name}"
payload = f"E2E placeholder media archive fixture {run_id}\n".encode("utf-8")
checksum = hashlib.sha256(payload).hexdigest()
media_root = Path(get_settings().media_root).resolve()
target = (media_root / relative_path).resolve()
if target != media_root and media_root not in target.parents:
    raise RuntimeError("Resolved media fixture path escaped media root")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(payload)

with db_session() as session:
    user_id = session.execute(
        text("SELECT id FROM app_users WHERE username = :username"),
        {"username": username},
    ).scalar_one()
    session.execute(
        text(
            """
            INSERT INTO media_assets (
              id, title, original_file_name, relative_path, source_relative_path,
              playback_relative_path, checksum_sha256, mime_type, file_size_bytes,
              upload_status, lifecycle_status, processing_phase, processing_progress,
              duration_seconds, width, height, uploaded_by, metadata, created_at, updated_at
            )
            VALUES (
              CAST(:id AS uuid), :title, :original_file_name, :relative_path, :relative_path,
              :relative_path, :checksum_sha256, 'video/mp4', :file_size_bytes,
              'ready', 'active', 'ready', 100,
              1, 16, 9, CAST(:uploaded_by AS uuid), CAST(:metadata AS jsonb), now(), now()
            )
            """
        ),
        {
            "id": asset_id,
            "title": title,
            "original_file_name": original_file_name,
            "relative_path": relative_path,
            "checksum_sha256": checksum,
            "file_size_bytes": len(payload),
            "uploaded_by": str(user_id),
            "metadata": json.dumps({"e2e": "media_archive", "run_id": run_id}, ensure_ascii=False),
        },
    )

print(json.dumps({
    "id": asset_id,
    "title": title,
    "original_file_name": original_file_name,
    "relative_path": relative_path,
    "checksum_sha256": checksum,
}))
`;
  return dockerPython(script, {
    E2E_MEDIA_ARCHIVE_RUN_ID: runId,
    E2E_MEDIA_ARCHIVE_USERNAME: username,
  });
}

async function createCatalogFixture(token, asset) {
  const chapters = await api("/api/chapters", token);
  const chapter =
    chapters.find((item) => item.chapter_id === "CH13") ||
    chapters.find((item) => item.chapter_id !== "CH00") ||
    chapters[0];
  if (!chapter) {
    throw new Error("No chapter is available for media archive E2E.");
  }

  const directoryTitle = `E2E media archive folder ${runId}`;
  const pointTitle = `E2E media archive point ${runId}`;
  const fixtureMetadata = { e2e: "media_archive", run_id: runId };

  const directory = await api("/api/admin/catalog/nodes", token, {
    method: "POST",
    body: {
      chapter_id: chapter.chapter_id,
      node_kind: "directory",
      title: directoryTitle,
      summary: "Temporary folder created by the media archive E2E test.",
      metadata: fixtureMetadata,
    },
  });
  const directoryNodeId = directory.node.node_id;

  const point = await api("/api/admin/catalog/nodes", token, {
    method: "POST",
    body: {
      chapter_id: chapter.chapter_id,
      parent_id: directoryNodeId,
      node_kind: "point",
      title: pointTitle,
      summary: "Temporary point created by the media archive E2E test.",
      metadata: fixtureMetadata,
    },
  });
  const pointNodeId = point.node.node_id;
  const canonicalPointId = point.node.canonical_point?.canonical_point_id || point.node.canonical_point_id;

  await api(`/api/admin/catalog/nodes/${encodeURIComponent(pointNodeId)}/point-content`, token, {
    method: "PUT",
    body: {
      point_title: pointTitle,
      principle_mode: "text",
      principle_text: `E2E principle text ${runId}`,
      phenomenon_explanation: `E2E phenomenon text ${runId}`,
      safety_note: `E2E safety note ${runId}`,
      metadata: fixtureMetadata,
    },
  });
  await api(`/api/admin/catalog/nodes/${encodeURIComponent(pointNodeId)}/point-content/publication`, token, {
    method: "POST",
    body: { action: "publish" },
  });
  await api(`/api/admin/catalog/nodes/${encodeURIComponent(directoryNodeId)}/status`, token, {
    method: "POST",
    body: { action: "publish" },
  });
  const binding = await api(`/api/admin/catalog/nodes/${encodeURIComponent(pointNodeId)}/media-bindings`, token, {
    method: "POST",
    body: {
      media_asset_id: asset.id,
      title: asset.title,
      metadata: fixtureMetadata,
    },
  });

  return {
    chapter_id: chapter.chapter_id,
    directory_node_id: directoryNodeId,
    directory_title: directoryTitle,
    point_node_id: pointNodeId,
    point_title: pointTitle,
    canonical_point_id: canonicalPointId,
    binding_id: binding.binding_id,
  };
}

function rebuildVideoLibraryIndex(label) {
  const result = spawnOrThrow(
    process.platform === "win32" ? "python" : "python3",
    ["scripts/rebuild_video_library_index.py", "--recreate"],
    {
      env: {
        ...process.env,
        VIDEO_LIBRARY_SEARCH_BACKEND: "elasticsearch",
        VIDEO_LIBRARY_SEARCH_URL: esUrl,
        VIDEO_LIBRARY_SEARCH_INDEX: esIndex,
      },
    },
    `Unable to rebuild Elasticsearch video library index during ${label}.`,
  );
  const lines = result.stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  return { label, stdout: lines };
}

async function readEsSources() {
  const response = await fetch(`${esUrl}/${encodeURIComponent(esIndex)}/_search`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ size: 1000, query: { match_all: {} } }),
  });
  if (!response.ok) {
    throw new Error(`Elasticsearch _search failed with HTTP ${response.status}: ${await response.text()}`);
  }
  const payload = await response.json();
  return (payload.hits?.hits || []).map((hit) => hit._source || {});
}

function findPointSource(sources, pointNodeId) {
  return sources.find((source) => source.id === pointNodeId || source.node_id === pointNodeId || source.placement_node_id === pointNodeId);
}

function assertEsHasNoMediaResourceFields(sources, forbiddenValues, label) {
  const serialized = JSON.stringify(sources);
  const leaked = forbiddenValues.filter((value) => value && serialized.includes(value));
  if (leaked.length) {
    throw new Error(`ES purity check failed during ${label}; leaked video-resource-only values: ${leaked.join(", ")}`);
  }
}

function inspectArchiveState(assetId, bindingId, pointNodeId) {
  const script = String.raw`
from __future__ import annotations

import datetime as dt
import decimal
import json
import os
import uuid

from sqlalchemy import text

from server.app.infrastructure.database import db_session

asset_id = os.environ["E2E_MEDIA_ARCHIVE_ASSET_ID"]
binding_id = os.environ["E2E_MEDIA_ARCHIVE_BINDING_ID"]
point_node_id = os.environ["E2E_MEDIA_ARCHIVE_POINT_NODE_ID"]

def normalize(value):
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, (dt.datetime, dt.date, decimal.Decimal, uuid.UUID)):
        return str(value)
    return value

with db_session() as session:
    asset = session.execute(
        text(
            """
            SELECT id, title, original_file_name, lifecycle_status, archived_at IS NOT NULL AS has_archived_at,
                   archive_reason, archive_metadata
            FROM media_assets
            WHERE id = CAST(:asset_id AS uuid)
            """
        ),
        {"asset_id": asset_id},
    ).mappings().one()
    binding = session.execute(
        text(
            """
            SELECT id, media_asset_id, binding_status, metadata
            FROM experiment_catalog_point_media_bindings
            WHERE id = CAST(:binding_id AS uuid)
            """
        ),
        {"binding_id": binding_id},
    ).mappings().one()
    detail = session.execute(
        text(
            """
            SELECT n.id AS point_node_id, n.status AS node_status, cp.status AS canonical_point_status,
                   pc.content_status, pc.point_title, pc.principle_text, pc.phenomenon_explanation,
                   pc.safety_note
            FROM experiment_catalog_nodes n
            LEFT JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
            LEFT JOIN experiment_catalog_point_content pc
              ON pc.node_id = n.id OR pc.canonical_point_id = n.canonical_point_id
            WHERE n.id = :point_node_id
            ORDER BY CASE pc.content_status WHEN 'published' THEN 0 WHEN 'draft' THEN 1 ELSE 2 END,
                     pc.updated_at DESC
            LIMIT 1
            """
        ),
        {"point_node_id": point_node_id},
    ).mappings().one()
    print(json.dumps({
        "asset": normalize(dict(asset)),
        "binding": normalize(dict(binding)),
        "point": normalize(dict(detail)),
    }, ensure_ascii=False))
`;
  return dockerPython(script, {
    E2E_MEDIA_ARCHIVE_ASSET_ID: assetId,
    E2E_MEDIA_ARCHIVE_BINDING_ID: bindingId,
    E2E_MEDIA_ARCHIVE_POINT_NODE_ID: pointNodeId,
  });
}

function cleanupOwnedMediaArchiveFixtures({ cleanupAll = false } = {}) {
  const script = String.raw`
from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings

run_id = os.environ.get("E2E_MEDIA_ARCHIVE_RUN_ID", "")
cleanup_all = os.environ.get("E2E_MEDIA_ARCHIVE_CLEANUP_ALL") == "1"
summary = {
    "cleanup_all": cleanup_all,
    "run_id": run_id,
    "nodes": [],
    "canonical_points": [],
    "assets": [],
    "files_deleted": [],
    "files_missing": [],
}
root = Path(get_settings().media_root).resolve()

with db_session() as session:
    node_rows = session.execute(
        text(
            """
            WITH RECURSIVE selected AS (
              SELECT id, parent_id, canonical_point_id, title
              FROM experiment_catalog_nodes
              WHERE COALESCE(metadata->>'e2e', '') = 'media_archive'
                AND (:cleanup_all OR metadata->>'run_id' = :run_id)
            ),
            subtree AS (
              SELECT id, parent_id, canonical_point_id, title FROM selected
              UNION ALL
              SELECT child.id, child.parent_id, child.canonical_point_id, child.title
              FROM experiment_catalog_nodes child
              JOIN subtree parent ON child.parent_id = parent.id
            )
            SELECT DISTINCT id, canonical_point_id, title
            FROM subtree
            ORDER BY id
            """
        ),
        {"cleanup_all": cleanup_all, "run_id": run_id},
    ).mappings().all()
    node_ids = [str(row["id"]) for row in node_rows]
    canonical_ids = sorted({str(row["canonical_point_id"]) for row in node_rows if row["canonical_point_id"]})
    summary["nodes"] = [{"id": str(row["id"]), "title": row["title"]} for row in node_rows]

    asset_rows = session.execute(
        text(
            """
            SELECT id, title, relative_path, source_relative_path, playback_relative_path, thumbnail_relative_path
            FROM media_assets
            WHERE COALESCE(metadata->>'e2e', '') = 'media_archive'
              AND (:cleanup_all OR metadata->>'run_id' = :run_id)
            ORDER BY created_at
            """
        ),
        {"cleanup_all": cleanup_all, "run_id": run_id},
    ).mappings().all()
    asset_ids = [str(row["id"]) for row in asset_rows]
    paths: set[str] = set()
    for row in asset_rows:
        summary["assets"].append({"id": str(row["id"]), "title": row["title"]})
        for key in ("relative_path", "source_relative_path", "playback_relative_path", "thumbnail_relative_path"):
            if row[key]:
                paths.add(str(row[key]))
    if asset_ids:
        extra_paths = session.execute(
            text(
                """
                SELECT relative_path
                FROM media_renditions
                WHERE media_asset_id::text = ANY(:asset_ids)
                UNION
                SELECT relative_path
                FROM media_video_fingerprints
                WHERE media_asset_id::text = ANY(:asset_ids)
                  AND relative_path IS NOT NULL
                """
            ),
            {"asset_ids": asset_ids},
        ).scalars().all()
        paths.update(str(path) for path in extra_paths if path)

    if node_ids:
        session.execute(text("DELETE FROM experiment_catalog_nodes WHERE id = ANY(:node_ids)"), {"node_ids": node_ids})
    if canonical_ids:
        deleted_canon = session.execute(
            text(
                """
                DELETE FROM experiment_catalog_points cp
                WHERE cp.id = ANY(:canonical_ids)
                  AND cp.title LIKE 'E2E media archive point %'
                  AND NOT EXISTS (
                    SELECT 1
                    FROM experiment_catalog_nodes n
                    WHERE n.canonical_point_id = cp.id
                  )
                RETURNING id, title
                """
            ),
            {"canonical_ids": canonical_ids},
        ).mappings().all()
        summary["canonical_points"] = [{"id": str(row["id"]), "title": row["title"]} for row in deleted_canon]
    if asset_ids:
        session.execute(text("DELETE FROM media_assets WHERE id::text = ANY(:asset_ids)"), {"asset_ids": asset_ids})

for relative in sorted(paths):
    target = (root / relative).resolve()
    if target != root and root in target.parents:
        if target.exists():
            target.unlink()
            summary["files_deleted"].append(relative)
        else:
            summary["files_missing"].append(relative)

print(json.dumps(summary, ensure_ascii=False))
`;
  return dockerPython(script, {
    E2E_MEDIA_ARCHIVE_RUN_ID: runId,
    E2E_MEDIA_ARCHIVE_CLEANUP_ALL: cleanupAll ? "1" : "0",
  });
}

async function cleanupFixture(token, fixture, asset) {
  const cleanup = { attempted: true, steps: [] };
  void token;
  void fixture;
  void asset;
  try {
    cleanup.database = cleanupOwnedMediaArchiveFixtures();
    cleanup.steps.push(
      `hard-deleted ${cleanup.database.nodes.length} catalog nodes and ${cleanup.database.assets.length} media assets`,
    );
  } catch (error) {
    cleanup.steps.push(`database cleanup failed: ${String(error)}`);
  }
  try {
    cleanup.rebuild = rebuildVideoLibraryIndex("cleanup");
  } catch (error) {
    cleanup.steps.push(`cleanup ES rebuild skipped: ${String(error)}`);
  }
  return cleanup;
}

async function archiveThroughUi(token, asset) {
  const launchOptions = { headless: true };
  const chromePath = candidateChromePaths()[0];
  if (chromePath) {
    launchOptions.executablePath = chromePath;
  }

  let browser;
  try {
    browser = await chromium.launch(launchOptions);
  } catch (error) {
    throw new Error(
      [
        `Unable to launch a Chromium browser: ${String(error)}`,
        "Set E2E_CHROME_PATH to a local Chrome/Edge executable or install Playwright browsers.",
      ].join("\n"),
    );
  }

  const diagnostics = {
    failedRequests: [],
    pageErrors: [],
    consoleMessages: [],
  };

  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 980 } });
    await context.addInitScript((accessToken) => {
      window.localStorage.setItem("chem_web_teacher_token", accessToken);
    }, token);
    context.on("requestfailed", (request) => {
      diagnostics.failedRequests.push({
        method: request.method(),
        resourceType: request.resourceType(),
        url: request.url(),
        failure: request.failure()?.errorText ?? "unknown",
      });
    });

    const page = await context.newPage();
    page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error)));
    page.on("console", (message) => {
      if (["error", "warning"].includes(message.type())) {
        diagnostics.consoleMessages.push({ type: message.type(), text: message.text() });
      }
    });

    await page.goto(`${baseUrl}/videos`, { waitUntil: "domcontentloaded", timeout: 45_000 });
    await page.locator(".video-drive-toolbar input").first().fill(asset.title, { timeout: 15_000 });
    await page.getByText(asset.title, { exact: true }).first().waitFor({ state: "visible", timeout: 20_000 });

    const assetContainer = page.locator("tr, .video-asset-card").filter({ hasText: asset.title }).first();
    await assetContainer.locator("button.ant-btn-dangerous").last().click({ timeout: 15_000 });

    const dialog = page.locator(".ant-modal").filter({ hasText: asset.title }).last();
    await dialog.waitFor({ state: "visible", timeout: 20_000 });
    const dialogText = await dialog.innerText({ timeout: 15_000 });
    if (!dialogText.includes("\u5f52\u6863") || !dialogText.includes(asset.title)) {
      throw new Error(`Archive confirmation did not identify the video asset. Dialog text: ${dialogText}`);
    }
    if (!dialogText.includes("\u5c06\u79fb\u9664 1 \u4e2a\u70b9\u4f4d\u89c6\u9891\u7ed1\u5b9a")) {
      throw new Error(`Archive confirmation did not warn about the bound catalog video. Dialog text: ${dialogText}`);
    }
    if (!dialogText.includes("\u70b9\u4f4d\u6587\u5b57\u5185\u5bb9")) {
      throw new Error(`Archive confirmation did not explain point content is preserved. Dialog text: ${dialogText}`);
    }

    await dialog.getByRole("button", { name: /\u5f52\u6863\u5e76\u79fb\u9664\u7ed1\u5b9a|\u5f52\u6863\u8d44\u6e90/ }).click();
    await dialog.waitFor({ state: "detached", timeout: 20_000 });
    await page.waitForFunction((title) => !document.body.innerText.includes(title), asset.title, { timeout: 20_000 });

    return { diagnostics };
  } finally {
    await browser.close().catch(() => undefined);
  }
}

async function main() {
  await requireHttpOk(`${apiBaseUrl}/health`, "backend");
  await requireHttpOk(`${baseUrl}/login`, "teacher frontend");
  await requireHttpOk(`${esUrl}/_cluster/health`, "elasticsearch");

  const bootstrap = bootstrapAdmin();
  const loginResponse = await login();
  const token = loginResponse.access_token;
  const preflightCleanup = cleanupOwnedMediaArchiveFixtures({ cleanupAll: true });
  const asset = seedMediaAsset();
  let fixture;
  let cleanup;
  const indexRuns = [];

  try {
    fixture = await createCatalogFixture(token, asset);
    const archivePlan = await api(`/api/admin/media/assets/${encodeURIComponent(asset.id)}/archive-plan`, token);
    if (archivePlan.catalog_binding_count !== 1 || archivePlan.student_visible_catalog_binding_count !== 1) {
      throw new Error(`Archive plan did not see exactly one student-visible catalog binding: ${JSON.stringify(archivePlan)}`);
    }

    indexRuns.push(rebuildVideoLibraryIndex("pre-archive assertion"));
    const sourcesBeforeArchive = await readEsSources();
    const pointBeforeArchive = findPointSource(sourcesBeforeArchive, fixture.point_node_id);
    if (!pointBeforeArchive) {
      throw new Error(`ES did not contain the published E2E point before archive: ${fixture.point_node_id}`);
    }
    if (pointBeforeArchive.has_video !== true || pointBeforeArchive.video_count !== 1) {
      throw new Error(`ES video flags before archive were wrong: ${JSON.stringify(pointBeforeArchive)}`);
    }
    assertEsHasNoMediaResourceFields(
      sourcesBeforeArchive,
      [asset.title, asset.original_file_name, asset.id, asset.relative_path, asset.checksum_sha256],
      "pre-archive assertion",
    );

    const ui = await archiveThroughUi(token, asset);
    const archiveState = inspectArchiveState(asset.id, fixture.binding_id, fixture.point_node_id);
    if (archiveState.asset.lifecycle_status !== "archived" || !archiveState.asset.has_archived_at) {
      throw new Error(`Media asset was not archived: ${JSON.stringify(archiveState.asset)}`);
    }
    if (archiveState.binding.binding_status !== "archived") {
      throw new Error(`Catalog binding was not archived: ${JSON.stringify(archiveState.binding)}`);
    }
    if (archiveState.binding.metadata?.archived_reason !== "media_asset_archived") {
      throw new Error(`Catalog binding archive metadata is missing media_asset_archived: ${JSON.stringify(archiveState.binding.metadata)}`);
    }
    if (archiveState.point.content_status !== "published" || archiveState.point.point_title !== fixture.point_title) {
      throw new Error(`Point content was not preserved after media archive: ${JSON.stringify(archiveState.point)}`);
    }

    const activeAssets = await api("/api/admin/media/assets?limit=500", token);
    if ((activeAssets.items || []).some((item) => item.id === asset.id)) {
      throw new Error("Archived media asset is still present in the default active media library API response.");
    }

    indexRuns.push(rebuildVideoLibraryIndex("post-archive assertion"));
    const sourcesAfterArchive = await readEsSources();
    const pointAfterArchive = findPointSource(sourcesAfterArchive, fixture.point_node_id);
    if (!pointAfterArchive) {
      throw new Error(`ES did not retain the published point document after archive: ${fixture.point_node_id}`);
    }
    if (pointAfterArchive.has_video !== false || pointAfterArchive.video_count !== 0) {
      throw new Error(`ES video flags after archive were wrong: ${JSON.stringify(pointAfterArchive)}`);
    }
    assertEsHasNoMediaResourceFields(
      sourcesAfterArchive,
      [asset.title, asset.original_file_name, asset.id, asset.relative_path, asset.checksum_sha256],
      "post-archive assertion",
    );

    cleanup = await cleanupFixture(token, fixture, asset);
    const summary = {
      ok: true,
      run_id: runId,
      baseUrl,
      apiBaseUrl,
      es: { url: esUrl, index: esIndex },
      username,
      bootstrap,
      preflight_cleanup: preflightCleanup,
      asset: { id: asset.id, title: asset.title },
      fixture,
      archive_plan: {
        catalog_binding_count: archivePlan.catalog_binding_count,
        student_visible_catalog_binding_count: archivePlan.student_visible_catalog_binding_count,
      },
      archive_state: archiveState,
      ui,
      index_runs: indexRuns,
      cleanup,
    };
    console.log(JSON.stringify(summary, null, 2));
  } catch (error) {
    cleanup = await cleanupFixture(token, fixture, asset).catch((cleanupError) => ({
      attempted: true,
      failed: String(cleanupError),
    }));
    console.error(
      JSON.stringify(
        {
          ok: false,
          run_id: runId,
          asset: asset ? { id: asset.id, title: asset.title } : null,
          fixture,
          preflight_cleanup: preflightCleanup,
          cleanup,
          error: error instanceof Error ? error.stack || error.message : String(error),
        },
        null,
        2,
      ),
    );
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exit(1);
});
