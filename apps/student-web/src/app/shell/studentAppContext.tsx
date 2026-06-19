import { createContext, useContext } from "react";
import type { AuthUser, StudentAppConfigResponse, StudentPosttestResponse } from "../../api";

export type StudentShellBaseContextValue = {
  user: AuthUser;
  onLogout: () => void | Promise<void>;
};

export type StudentRuntimeContextValue = StudentShellBaseContextValue & {
  appConfig: StudentAppConfigResponse;
  configError: string;
  canUseAssistant: boolean;
  canUseFeedback: boolean;
  startAssessmentSession: () => Promise<StudentPosttestResponse | null>;
  posttestLoading: boolean;
  posttestError: string;
};

const StudentShellBaseContext = createContext<StudentShellBaseContextValue | null>(null);
const StudentRuntimeContext = createContext<StudentRuntimeContextValue | null>(null);

export const StudentShellBaseProvider = StudentShellBaseContext.Provider;
export const StudentRuntimeProvider = StudentRuntimeContext.Provider;

export function useStudentShellBase(): StudentShellBaseContextValue {
  const value = useContext(StudentShellBaseContext);
  if (!value) throw new Error("Student shell base context is missing");
  return value;
}

export function useStudentRuntime(): StudentRuntimeContextValue {
  const value = useContext(StudentRuntimeContext);
  if (!value) throw new Error("Student runtime context is missing");
  return value;
}
