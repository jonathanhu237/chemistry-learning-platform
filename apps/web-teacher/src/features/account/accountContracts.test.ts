import { describe, expect, it } from "vitest";

import accountApiSource from "../../api/teacherAccounts.ts?raw";
import requireAdminSource from "../../app/auth/RequireAdmin.tsx?raw";
import adminHeaderSource from "../../app/shell/AdminHeader.tsx?raw";
import passwordFormSource from "./PasswordChangeForm.tsx?raw";
import accountCardSource from "./TeacherAccountManagementCard.tsx?raw";
import { teacherRoleLabel } from "../../app/shell/AdminHeader";

describe("teacher account administration contracts", () => {
  it("uses the supervisor-owned account lifecycle endpoints without destructive account editing", () => {
    expect(accountApiSource).toContain('"/api/admin/teacher-accounts"');
    expect(accountApiSource).toContain("/reset-password`");
    expect(accountApiSource).toContain("/disable`");
    expect(accountApiSource).toContain("/enable`");
    expect(accountApiSource).toContain("encodeURIComponent(accountId)");
    expect(accountApiSource).not.toContain('method: "DELETE"');
    expect(accountApiSource).not.toContain('method: "PATCH"');
  });

  it("creates only ordinary teacher accounts with forced first-login password rotation", () => {
    expect(accountCardSource).toContain("新建教师账号");
    expect(accountCardSource).toContain("首次登录都必须修改密码");
    expect(accountCardSource).not.toContain('name="role"');
    expect(accountCardSource).not.toContain('name="must_change_password"');
  });

  it("forces password rotation before rendering the teacher console and replaces the session", () => {
    expect(requireAdminSource).toContain("meQuery.data.must_change_password");
    expect(requireAdminSource).toContain("<ForcedPasswordChangePage");
    expect(requireAdminSource).toContain("onLogout={logout}");
    expect(requireAdminSource).toContain("setAuthToken(response.access_token)");
    expect(passwordFormSource).toContain("current_password");
    expect(passwordFormSource).toContain("new_password");
  });

  it("presents the internal admin role as supervisor teacher and keeps self-service password change", () => {
    expect(teacherRoleLabel("admin")).toBe("主管教师");
    expect(teacherRoleLabel("teacher")).toBe("教师");
    expect(adminHeaderSource).toContain("修改密码");
    expect(accountCardSource).toContain("请从右上角修改自己的密码");
    expect(accountCardSource).toContain("现有会话会立即失效");
  });
});
