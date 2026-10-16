import { useEffect, useState } from "react";
import {
  ComputerDesktopIcon,
  MoonIcon,
  SunIcon,
} from "@heroicons/react/24/outline";
import {
  applyTheme,
  persistTheme,
  readStoredTheme,
  type ThemeMode,
} from "../lib/theme";

const OPTIONS: {
  mode: ThemeMode;
  label: string;
  Icon: typeof SunIcon;
}[] = [
  { mode: "system", label: "System", Icon: ComputerDesktopIcon },
  { mode: "light", label: "Light", Icon: SunIcon },
  { mode: "dark", label: "Dark", Icon: MoonIcon },
];

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const [mode, setMode] = useState<ThemeMode>(() => readStoredTheme());

  useEffect(() => {
    applyTheme(mode);
    if (mode !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyTheme("system");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [mode]);

  function select(next: ThemeMode) {
    setMode(next);
    persistTheme(next);
  }

  return (
    <div
      className={[
        "flex gap-1 rounded-lg border border-slate-200 p-0.5 dark:border-gray-800",
        compact ? "" : "ml-auto",
      ].join(" ")}
      role="group"
      aria-label="Color theme"
    >
      {OPTIONS.map(({ mode: m, label, Icon }) => {
        const checked = mode === m;
        return (
          <button
            key={m}
            type="button"
            aria-label={label}
            title={label}
            aria-pressed={checked}
            data-state={checked ? "checked" : "unchecked"}
            onClick={() => select(m)}
            className="group relative flex size-8 appearance-none items-center justify-center outline-none"
          >
            <span
              className={[
                "flex size-full shrink-0 items-center justify-center rounded-lg",
                "text-gray-700 dark:text-gray-400",
                "bg-transparent",
                "group-data-[state=checked]:bg-indigo-50 group-data-[state=checked]:text-indigo-600",
                "dark:group-data-[state=checked]:bg-indigo-500/20 dark:group-data-[state=checked]:text-indigo-300",
              ].join(" ")}
            >
              <Icon className="size-4" aria-hidden="true" />
            </span>
          </button>
        );
      })}
    </div>
  );
}
