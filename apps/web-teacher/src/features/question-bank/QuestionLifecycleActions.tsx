import { RollbackOutlined, StopOutlined } from "@ant-design/icons";
import { Button, Popconfirm, Space, Typography } from "antd";
import type { MouseEvent } from "react";

import type { Question } from "../../api/questionBank";

const { Text } = Typography;

export type QuestionLifecycleAction = "withdraw" | "disable";

type Props = {
  question: Pick<Question, "id" | "status">;
  busyAction?: QuestionLifecycleAction | null;
  onWithdraw: (questionId: string) => void;
  onDisable: (questionId: string) => void;
};

export function QuestionLifecycleActions({ question, busyAction, onWithdraw, onDisable }: Props) {
  const stopRowClick = (event: MouseEvent<HTMLElement>) => event.stopPropagation();

  if (question.status === "disabled") {
    return <Text type="secondary">已停用</Text>;
  }

  return (
    <Space size={2} wrap className="question-lifecycle-actions" onClick={stopRowClick}>
      {question.status === "published" ? (
        <Popconfirm
          title="撤回这道已发布题目并进入修订？"
          description="题目会暂时从学生端停用，并生成唯一待审草稿；重新发布后仍沿用原题。"
          okText="确认撤回"
          cancelText="取消"
          onConfirm={() => onWithdraw(question.id)}
          disabled={Boolean(busyAction)}
        >
          <Button
            type="link"
            size="small"
            icon={<RollbackOutlined />}
            loading={busyAction === "withdraw"}
            disabled={Boolean(busyAction && busyAction !== "withdraw")}
          >
            撤回修改
          </Button>
        </Popconfirm>
      ) : null}
      <Popconfirm
        title="停用这道题目？"
        description="只停用题目，不会生成修订草稿。"
        okText="确认停用"
        cancelText="取消"
        okButtonProps={{ danger: true }}
        onConfirm={() => onDisable(question.id)}
        disabled={Boolean(busyAction)}
      >
        <Button
          type="link"
          danger
          size="small"
          icon={<StopOutlined />}
          loading={busyAction === "disable"}
          disabled={Boolean(busyAction && busyAction !== "disable")}
        >
          停用
        </Button>
      </Popconfirm>
    </Space>
  );
}
