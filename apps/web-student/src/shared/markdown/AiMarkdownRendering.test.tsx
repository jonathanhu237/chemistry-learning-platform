import "@testing-library/jest-dom/vitest";
import { StrictMode } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AiStaticMarkdown } from "../../components/AiMarkdown";
import { AiMessageMarkdown } from "./AiMessageMarkdown";
import { extractAiRichContentArtifacts } from "./aiRichContentArtifacts";
import { normalizeStudentMarkdown } from "./markdownNormalize";

afterEach(() => cleanup());

function visibleKatexText(container: HTMLElement): string {
  return Array.from(container.querySelectorAll(".katex-html"))
    .map((element) => element.textContent || "")
    .join(" ");
}

describe("student chemistry Markdown rendering", () => {
  it("extracts stable rich-content artifacts from completed Markdown", () => {
    const answer = [
      "| 试剂 | 现象 |",
      "|---|---|",
      "| KBr | 生成 $\\ce{Br2}$ |",
      "",
      "```mermaid",
      "flowchart TD",
      "  A[观察] --> B[判断]",
      "```",
      "",
      "| 步骤 | 判断 |",
      "|---|---|",
      "| 加入 CCl4 | 下层变橙色 |",
    ].join("\n");

    const artifacts = extractAiRichContentArtifacts(answer, "assistant-message-1");

    expect(artifacts.map((artifact) => `${artifact.kind}:${artifact.id}`)).toEqual([
      "table:assistant-message-1-table-1",
      "mermaid:assistant-message-1-mermaid-1",
      "table:assistant-message-1-table-2",
    ]);
    expect(artifacts[0].table?.headers).toEqual(["试剂", "现象"]);
    expect(artifacts[1].source).toContain("flowchart TD");
  });

  it("renders static GFM, math, and mhchem content", async () => {
    const answer = [
      "### 常见气体检验",
      "",
      "| 气体 | 检验方法 | 现象 |",
      "|---|---|---|",
      "| CO2 | 通入澄清石灰水 | 变浑浊 |",
      "| NH3 | 湿润红色石蕊试纸 | 变蓝 |",
      "",
      "- [x] 观察现象",
      "- [ ] 书写方程式",
      "",
      "酸度计算：$pH=-\\log[H^+]$",
      "",
      "$$K_a=\\frac{[H^+][A^-]}{[HA]}$$",
      "",
      "反应：$\\ce{2H2 + O2 -> 2H2O}$",
    ].join("\n");

    const { container } = render(<AiStaticMarkdown text={answer} />);

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("CO2")).toBeInTheDocument();
    expect(container.querySelector(".ai-md-task-checkbox")).not.toBeNull();
    await waitFor(() => expect(container.querySelector(".katex")).not.toBeNull());
    expect(container.querySelector(".katex-error")).toBeNull();
    expect(visibleKatexText(container)).not.toContain("\\ce");
  });

  it("keeps alternate math normalization outside fenced blocks", () => {
    const markdown = ["```mermaid", "flowchart TD", "  A[\\(不应转换\\)] --> B[保留]", "```", "", "普通公式：\\(x+y\\)"].join("\n");

    expect(normalizeStudentMarkdown(markdown)).toContain("A[\\(不应转换\\)]");
    expect(normalizeStudentMarkdown(markdown)).toContain("普通公式：$x+y$");
  });

  it("renders a static Mermaid block with a mobile-safe container or fallback", async () => {
    const answer = ["```mermaid", "flowchart TD", "  A[加入试剂] --> B{是否变色}", "  B -->|是| C[记录现象]", "```"].join("\n");

    const { container } = render(<AiStaticMarkdown text={answer} />);

    await waitFor(() => expect(container.querySelector('[data-streamdown="mermaid-block"]')).not.toBeNull());
    expect(container.textContent).toMatch(/mermaid|流程图/);
  });

  it("adds rich-content controls only for completed static assistant artifacts", async () => {
    const onOpenArtifact = vi.fn();
    const answer = [
      "| 试剂 | 现象 |",
      "|---|---|",
      "| KBr | 生成 $\\ce{Br2}$ |",
      "",
      "```mermaid",
      "flowchart TD",
      "  A[观察] --> B[判断]",
      "```",
    ].join("\n");

    render(
      <AiMessageMarkdown
        text={answer}
        streaming={false}
        artifactContext={{
          historyId: "history-1",
          messageId: "assistant-message-1",
          onOpenArtifact,
        }}
      />,
    );

    const tableDetail = screen.getByRole("button", { name: "查看表格 1: 试剂" });
    fireEvent.click(tableDetail);
    expect(onOpenArtifact).toHaveBeenCalledWith(expect.objectContaining({ id: "assistant-message-1-table-1", kind: "table" }));
    expect(await screen.findByRole("button", { name: "查看流程图 1" })).toBeInTheDocument();

    cleanup();
    render(
      <AiMessageMarkdown
        text={answer}
        streaming
        artifactContext={{
          historyId: "history-1",
          messageId: "assistant-message-1",
          onOpenArtifact,
        }}
      />,
    );
    expect(screen.queryByRole("button", { name: /查看/ })).toBeNull();
  });

  it("keeps rich-content controls stable under StrictMode rendering", async () => {
    const answer = [
      "| 试剂 | 现象 |",
      "|---|---|",
      "| KBr | 生成 Br2 |",
      "",
      "```mermaid",
      "flowchart TD",
      "  A[观察] --> B[判断]",
      "```",
      "",
      "| 步骤 | 判断 |",
      "|---|---|",
      "| 加入 CCl4 | 下层变橙色 |",
    ].join("\n");

    render(
      <StrictMode>
        <AiMessageMarkdown
          text={answer}
          artifactContext={{
            historyId: "history-strict",
            messageId: "assistant-message-strict",
            onOpenArtifact: vi.fn(),
          }}
        />
      </StrictMode>,
    );

    expect(screen.getByRole("button", { name: "查看表格 1: 试剂" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "查看表格 2: 步骤" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "查看流程图 1" })).toBeInTheDocument();
  });

  it("uses the Streamdown facade for active streaming answers", async () => {
    const answer = ["### 正在组织", "", "| 步骤 | 现象 |", "|---|---|", "| 1 | 溶液变色 |", "", "$\\ce{Cl2 + 2Br- -> 2Cl- + Br2}$"].join("\n");

    const { container } = render(<AiMessageMarkdown text={answer} streaming />);

    await waitFor(() => expect(container.querySelector(".ai-markdown-streaming")).not.toBeNull());
    expect(screen.getByText("正在组织")).toBeInTheDocument();
  });

  it("renders mhchem in streaming answers without leaking the raw ce command", async () => {
    const answer = "反应：$\\ce{Cl2 + 2Br- -> 2Cl- + Br2}$";

    const { container } = render(<AiMessageMarkdown text={answer} streaming />);

    await waitFor(() => expect(container.querySelector(".ai-markdown-streaming .katex-html")).not.toBeNull());
    expect(visibleKatexText(container)).not.toContain("\\ce");
  });
});
