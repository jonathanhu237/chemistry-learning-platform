import { describe, expect, it } from "vitest";

import questionBankApiSource from "../../api/questionBank.ts?raw";
import questionBankPageSource from "./QuestionBanksPage.tsx?raw";

describe("published question withdrawal contracts", () => {
  it("posts to the withdrawal endpoint and models immutable source provenance", () => {
    expect(questionBankApiSource).toContain("withdrawQuestionToDraft");
    expect(questionBankApiSource).toContain("/revoke-to-draft");
    expect(questionBankApiSource).toContain("revoked_from_question_id");
    expect(questionBankApiSource).toContain("withdrawal?:");
  });

  it("opens the returned unique draft and keeps disable independent", () => {
    expect(questionBankPageSource).toContain("withdrawQuestionToDraft(questionId)");
    expect(questionBankPageSource).toContain("setDraftEditor({");
    expect(questionBankPageSource).toContain("已撤回，修订草稿已打开");
    expect(questionBankPageSource).toContain("disableQuestion(questionId)");
    expect(questionBankPageSource).toContain("发布后会更新原题并恢复启用");
  });
});
