import { useCallback, useEffect, useState } from "react";
import { Atom, Clock3, Trash2, X } from "lucide-react";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { defaultAssistantContext } from "../../features/assistant/assistantContext";
import {
  clearStudentAiHistory,
  deleteStudentAiHistory,
  listStudentAiHistory,
  readStudentAiHistory,
  type StudentAiHistoryEntry,
} from "../../features/assistant/assistantHistoryStore";
import { StudentAiChatTab } from "../../features/assistant/StudentAiChatTab";
import { MobileEmptyState } from "../../mobile/primitives";

function formatHistoryTime(value: string): string {
  const time = new Date(value);
  if (Number.isNaN(time.getTime())) return "";
  return time.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function AiHistoryPanel({
  open,
  entries,
  selectedId,
  onClose,
  onSelect,
  onDelete,
  onClear,
}: {
  open: boolean;
  entries: StudentAiHistoryEntry[];
  selectedId?: string | null;
  onClose: () => void;
  onSelect: (entry: StudentAiHistoryEntry) => void;
  onDelete: (id: string) => void;
  onClear: () => void;
}) {
  if (!open) return null;
  return (
    <div className="ai-history-layer" role="dialog" aria-modal="true" aria-label="Atom 历史记录">
      <button type="button" className="ai-history-backdrop" onClick={onClose} aria-label="关闭 Atom 历史记录背景" />
      <section className="ai-history-sheet">
        <header className="ai-history-head">
          <div>
            <p>近期对话</p>
            <h2>Atom 历史记录</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="关闭 Atom 历史记录">
            <X size={18} />
          </button>
        </header>

        {entries.length ? (
          <>
            <div className="ai-history-list">
              {entries.map((entry) => (
                <article className={entry.id === selectedId ? "ai-history-item selected" : "ai-history-item"} key={entry.id}>
                  <button type="button" className="ai-history-main" onClick={() => onSelect(entry)}>
                    <strong>{entry.title}</strong>
                    <span>{entry.contextTitle}</span>
                    <small>
                      <Clock3 size={12} />
                      {formatHistoryTime(entry.updatedAt)}
                    </small>
                  </button>
                  <button type="button" className="ai-history-delete" onClick={() => onDelete(entry.id)} aria-label="删除这条 Atom 历史记录">
                    <Trash2 size={15} />
                  </button>
                </article>
              ))}
            </div>
            <button type="button" className="ai-history-clear" onClick={onClear}>
              清空历史记录
            </button>
          </>
        ) : (
          <div className="ai-history-empty">
            <Atom size={18} />
            <strong>还没有历史记录</strong>
            <span>从主 Atom 页或课程上下文发起提问后，会保存在这里。</span>
          </div>
        )}
      </section>
    </div>
  );
}

export function AiRootPage() {
  const { canUseAssistant } = useStudentRuntime();
  const context = defaultAssistantContext();
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyEntries, setHistoryEntries] = useState<StudentAiHistoryEntry[]>([]);
  const [selectedHistory, setSelectedHistory] = useState<StudentAiHistoryEntry | null>(null);

  const refreshHistory = useCallback(() => {
    setHistoryEntries(listStudentAiHistory());
  }, []);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  const openHistory = () => {
    refreshHistory();
    setHistoryOpen(true);
  };

  const selectHistory = (entry: StudentAiHistoryEntry) => {
    setSelectedHistory(readStudentAiHistory(entry.id) || entry);
    setHistoryOpen(false);
  };

  const deleteHistory = (id: string) => {
    deleteStudentAiHistory(id);
    if (selectedHistory?.id === id) setSelectedHistory(null);
    refreshHistory();
  };

  const clearHistory = () => {
    clearStudentAiHistory();
    setSelectedHistory(null);
    refreshHistory();
  };

  return (
    <section className="ai-root-page" aria-label="Atom 中心">
      {canUseAssistant ? (
        <>
          <StudentAiChatTab
            context={context}
            onResetContext={() => setSelectedHistory(null)}
            variant="root"
            historyEntry={selectedHistory}
            onOpenHistory={openHistory}
            onHistoryChange={refreshHistory}
          />
          <AiHistoryPanel
            open={historyOpen}
            entries={historyEntries}
            selectedId={selectedHistory?.id}
            onClose={() => setHistoryOpen(false)}
            onSelect={selectHistory}
            onDelete={deleteHistory}
            onClear={clearHistory}
          />
        </>
      ) : (
        <section className="learning-panel">
          <MobileEmptyState className="empty-learning-card" icon={<Atom size={20} />}>
            <span>Atom 学习助手暂未开放</span>
          </MobileEmptyState>
        </section>
      )}
    </section>
  );
}
