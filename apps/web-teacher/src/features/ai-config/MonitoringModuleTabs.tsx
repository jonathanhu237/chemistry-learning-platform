import type { MonitorModuleKey } from "./monitoringTypes";
import { monitorModules } from "./monitoringMappers";

type MonitoringModuleTabsProps = {
  activeKey: MonitorModuleKey;
  onChange: (key: MonitorModuleKey) => void;
};

export function MonitoringModuleTabs({ activeKey, onChange }: MonitoringModuleTabsProps) {
  return (
    <div className="ai-monitor-tabs" role="tablist" aria-label="智能监控模块">
      {monitorModules.map((module) => (
        <button
          key={module.key}
          type="button"
          role="tab"
          aria-selected={activeKey === module.key}
          className={activeKey === module.key ? "ai-monitor-tab ai-monitor-tab-active" : "ai-monitor-tab"}
          onClick={() => onChange(module.key)}
        >
          <span>{module.label}</span>
        </button>
      ))}
    </div>
  );
}
