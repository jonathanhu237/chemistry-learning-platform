import { Atom, BookOpenCheck, ClipboardList, Home, UserRound } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { rootPathById } from "../router/routeVisibility";
import type { StudentRootRouteId } from "../router/routeTypes";

const navItems: Array<{ id: StudentRootRouteId; label: string; icon: ReactNode }> = [
  { id: "home", label: "首页", icon: <Home size={20} /> },
  { id: "learn", label: "学习", icon: <BookOpenCheck size={20} /> },
  { id: "ai", label: "Atom", icon: <Atom size={21} /> },
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
          className={[
            "student-bottom-nav-item",
            item.id === "ai" ? "student-bottom-nav-primary" : "student-bottom-nav-standard",
            activeRoot === item.id ? "active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          aria-label={item.label}
          aria-current={activeRoot === item.id ? "page" : undefined}
          data-root={item.id}
          onClick={() => {
            void navigate({ to: rootPathById[item.id] });
            window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" }));
          }}
        >
          <span className="student-bottom-nav-label">{item.label}</span>
          <span className="student-bottom-nav-icon" aria-hidden="true">
            {item.icon}
          </span>
        </button>
      ))}
    </nav>
  );
}
