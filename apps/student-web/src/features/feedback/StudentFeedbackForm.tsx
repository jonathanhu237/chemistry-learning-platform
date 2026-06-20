import { FormEvent, useEffect, useRef, useState } from "react";
import { LoaderCircle, Paperclip, Send, Trash2 } from "lucide-react";
import { errorMessage, submitStudentFeedback } from "../../api";
import { MobileButton, MobileTextArea } from "../../mobile/primitives";
import { feedbackTypes, type FeedbackContext } from "./feedbackTypes";

export function StudentFeedbackForm({ context }: { context: FeedbackContext }) {
  const [feedbackType, setFeedbackType] = useState("content");
  const [content, setContent] = useState("");
  const [attachment, setAttachment] = useState<File | null>(null);
  const [attachmentError, setAttachmentError] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setMessage("");
    setError("");
  }, [context.pagePath, context.experimentId, context.pointNodeId]);

  const selectAttachment = (file: File | null) => {
    setAttachmentError("");
    if (!file) {
      setAttachment(null);
      return;
    }
    const allowedTypes = new Set(["image/png", "image/jpeg", "image/webp"]);
    if (!allowedTypes.has(file.type)) {
      setAttachment(null);
      setAttachmentError("只能上传 PNG、JPG 或 WebP 图片");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setAttachment(null);
      setAttachmentError("图片不能超过 5 MB");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    setAttachment(file);
  };

  const clearAttachment = () => {
    setAttachment(null);
    setAttachmentError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || attachmentError || loading) return;
    setLoading(true);
    setMessage("");
    setError("");
    try {
      await submitStudentFeedback({
        feedback_type: feedbackType,
        content: trimmed,
        chapter_id: context.chapterId,
        experiment_id: context.experimentId,
        point_node_id: context.pointNodeId,
        catalog_path: context.catalogPath,
        page_path: context.pagePath,
        metadata: {
          ...context.metadata,
          context_title: context.contextTitle,
          viewport: { width: window.innerWidth, height: window.innerHeight },
          user_agent: window.navigator.userAgent,
        },
        attachment,
      });
      setContent("");
      clearAttachment();
      setMessage("已收到反馈，老师后台可以看到。");
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="feedback-panel profile-feedback-panel" onSubmit={submit} aria-label="学生端反馈">
      <header className="feedback-head">
        <div>
          <span>反馈</span>
          <h2>{context.contextTitle}</h2>
        </div>
      </header>
      <div className="feedback-type-row">
        {feedbackTypes.map((item) => (
          <button
            key={item.value}
            type="button"
            className={feedbackType === item.value ? "active" : ""}
            onClick={() => setFeedbackType(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <MobileTextArea
        value={content}
        rows={4}
        maxLength={4000}
        placeholder="描述你遇到的问题或建议，可以配一张截图"
        onChange={(event) => setContent(event.target.value)}
      />
      <div className="feedback-attachment-row">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={(event) => selectAttachment(event.target.files?.[0] ?? null)}
        />
        <button type="button" disabled={loading} onClick={() => fileInputRef.current?.click()}>
          <Paperclip size={15} />
          <span>{attachment ? "更换图片" : "添加截图"}</span>
        </button>
        {attachment ? (
          <button type="button" className="feedback-file-pill" disabled={loading} onClick={clearAttachment}>
            <span>{attachment.name}</span>
            <Trash2 size={14} />
          </button>
        ) : null}
      </div>
      {attachmentError ? <div className="form-error">{attachmentError}</div> : null}
      {message ? <div className="form-hint feedback-success">{message}</div> : null}
      {error ? <div className="form-error">{error}</div> : null}
      <MobileButton className="primary-action" type="submit" loading={loading} disabled={!content.trim() || Boolean(attachmentError)}>
        {loading ? <LoaderCircle className="spin" size={18} /> : <Send size={18} />}
        <span>{loading ? "正在提交" : "提交反馈"}</span>
      </MobileButton>
    </form>
  );
}
