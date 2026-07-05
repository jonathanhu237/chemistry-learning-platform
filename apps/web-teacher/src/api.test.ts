import { describe, expect, it } from "vitest";

import { ApiError, legacyTeacherErrorMessage } from "./api";

describe("legacyTeacherErrorMessage", () => {
  it("renders FastAPI default password validation errors as actionable Chinese text", () => {
    const error = new ApiError(422, [
      {
        type: "string_too_short",
        loc: ["body", "default_password"],
        msg: "String should have at least 6 characters",
        ctx: { min_length: 6 },
      },
    ]);

    expect(legacyTeacherErrorMessage(error)).toBe("统一初始密码至少需要 6 位。");
  });
});
