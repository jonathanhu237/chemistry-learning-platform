import { BookOpenCheck, ClipboardList, Home, MessageCircle, UserRound } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { rootPathById } from "../router/routeVisibility";
import type { StudentRootRouteId } from "../router/routeTypes";

const navItems: Array<{ id: StudentRootRouteId; label: string; icon: ReactNode }> = [
  { id: "home", label: "首页", icon: <Home size={20} /> },
  { id: "learn", label: "学习", icon: <BookOpenCheck size={20} /> },
  { id: "ai", label: "AI", icon: <MessageCircle size={21} /> },
  { id: "assessment", label: "测评", icon: <ClipboardList size={20} /> },
  { id: "profile", label: "我的", icon: <UserRound size={20} /> },
];

export function StudentBottomNav({ activeRoot }: { activeRoot: StudentRootRouteId }) {
  const navigate = useNavigate();
  return (
    <nav className="student-bottom-nav" aria-label="学生端主导航">
      {navItems.map((item) => (
        <button
          key={item.id}
          type="button"
          className={activeRoot === item.id ? "active" : ""}
          aria-current={activeRoot === item.id ? "page" : undefined}
          data-root={item.id}
          onClick={() => {
            void navigate({ to: rootPathById[item.id] });
            window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" }));
          }}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
