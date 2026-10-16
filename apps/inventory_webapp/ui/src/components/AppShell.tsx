import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { UserCircleIcon } from "@heroicons/react/24/outline";
import { api, Project } from "../api";
import { RiserMark } from "./RiserMark";
import { ThemeToggle } from "./ThemeToggle";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsOpen, setProjectsOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const navRef = useRef<HTMLElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.projects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!navRef.current?.contains(e.target as Node)) {
        setProjectsOpen(false);
        setUserOpen(false);
      }
    }
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-950">
      <header
        ref={navRef}
        className="border-b border-slate-200 bg-white dark:border-gray-800 dark:bg-gray-950/80 dark:backdrop-blur"
      >
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3">
          <NavLink
            to="/"
            end
            className="mr-6 flex shrink-0 items-center gap-2.5 no-underline text-slate-900 dark:text-gray-100 sm:mr-10"
            onClick={() => {
              setProjectsOpen(false);
              setUserOpen(false);
            }}
          >
            <RiserMark className="h-7 w-7 sm:h-8 sm:w-8" />
            <span className="flex flex-col">
              <span className="text-base font-semibold tracking-tight sm:text-lg">
                Riser
              </span>
              <span className="text-xs font-medium text-slate-500 dark:text-gray-400">
                Inventory review
              </span>
            </span>
          </NavLink>

          <nav className="flex flex-wrap items-center gap-1 text-sm">
            <div className="relative">
              <button
                type="button"
                className={[
                  "rounded-lg px-3 py-1.5 font-medium",
                  projectsOpen
                    ? "bg-slate-900 text-white dark:bg-indigo-500"
                    : "text-slate-700 hover:bg-slate-100 dark:text-gray-300 dark:hover:bg-white/5",
                ].join(" ")}
                onClick={(e) => {
                  e.stopPropagation();
                  setProjectsOpen((v) => !v);
                  setUserOpen(false);
                }}
              >
                Projects ▾
              </button>
              {projectsOpen && (
                <div className="absolute left-0 top-[calc(100%+0.4rem)] z-50 w-80 rounded-xl border border-slate-200 bg-white p-2 shadow-lg dark:border-gray-700 dark:bg-gray-900">
                  <div className="px-2 py-1 obs-label-upper">
                    All projects
                  </div>
                  {projects.length === 0 && (
                    <div className="px-2 py-2 text-sm text-slate-500 dark:text-gray-400">
                      No projects yet
                    </div>
                  )}
                  {projects.map((p) => (
                    <button
                      key={p.uuid}
                      type="button"
                      className="w-full rounded-lg px-2 py-2 text-left hover:bg-slate-50 dark:hover:bg-white/5"
                      onClick={() => {
                        setProjectsOpen(false);
                        navigate(`/projects/${p.uuid}`);
                      }}
                    >
                      <div className="text-sm font-semibold text-slate-900 dark:text-gray-100">
                        {p.title_block?.display_name || p.name}
                      </div>
                      <div className="mt-0.5 text-xs text-slate-500 dark:text-gray-400">
                        {[
                          p.client || p.title_block?.client,
                          p.architect || p.title_block?.architect,
                          p.owner,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </div>
                    </button>
                  ))}
                  <Link
                    to="/"
                    className="mt-1 block rounded-lg px-2 py-2 text-sm font-medium text-blue-600 hover:bg-slate-50 dark:text-blue-400 dark:hover:bg-white/5"
                    onClick={() => setProjectsOpen(false)}
                  >
                    View all projects →
                  </Link>
                </div>
              )}
            </div>
            <NavLink
              to="/catalogue"
              className={({ isActive }) =>
                [
                  "rounded-lg px-3 py-1.5 font-medium no-underline",
                  isActive
                    ? "bg-slate-900 text-white dark:bg-indigo-500"
                    : "text-slate-700 hover:bg-slate-100 dark:text-gray-300 dark:hover:bg-white/5",
                ].join(" ")
              }
              onClick={() => {
                setProjectsOpen(false);
                setUserOpen(false);
              }}
            >
              Catalogue
            </NavLink>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <ThemeToggle />
            <div className="relative">
              <button
                type="button"
                aria-label="Account menu"
                className={[
                  "inline-flex items-center rounded-lg p-1.5",
                  userOpen
                    ? "bg-slate-900 text-white dark:bg-indigo-500"
                    : "text-slate-600 hover:bg-slate-100 dark:text-gray-300 dark:hover:bg-white/5",
                ].join(" ")}
                onClick={(e) => {
                  e.stopPropagation();
                  setUserOpen((v) => !v);
                  setProjectsOpen(false);
                }}
              >
                <UserCircleIcon className="h-7 w-7" />
              </button>
              {userOpen && (
                <div className="absolute right-0 top-[calc(100%+0.4rem)] z-50 w-72 rounded-xl border border-slate-200 bg-white p-2 shadow-lg dark:border-gray-700 dark:bg-gray-900">
                  <div className="flex items-center gap-3 px-2 py-2">
                    <UserCircleIcon className="h-10 w-10 text-slate-400" />
                    <div>
                      <div className="text-sm font-semibold text-slate-900 dark:text-gray-100">
                        Seneca user
                      </div>
                      <div className="text-xs text-slate-500 dark:text-gray-400">
                        reviewer@senecagrp.com
                      </div>
                    </div>
                  </div>
                  <div className="my-1 border-t border-slate-100 dark:border-gray-800" />
                  <div className="px-2 py-1 obs-label-upper">
                    Organisation
                  </div>
                  <div className="px-2 py-1 text-sm text-slate-700 dark:text-gray-300">
                    Seneca Group Ltd
                  </div>
                  <div className="my-1 border-t border-slate-100 dark:border-gray-800" />
                  <div className="px-2 py-1 obs-label-upper">
                    Options
                  </div>
                  <div className="px-2 py-2">
                    <div className="mb-1 text-xs text-slate-500 dark:text-gray-400">
                      Appearance
                    </div>
                    <ThemeToggle compact />
                  </div>
                  <div className="my-1 border-t border-slate-100 dark:border-gray-800" />
                  <button
                    type="button"
                    disabled
                    className="w-full rounded-lg px-2 py-2 text-left text-sm text-slate-400"
                  >
                    Account settings (soon)
                  </button>
                  <button
                    type="button"
                    disabled
                    className="w-full rounded-lg px-2 py-2 text-left text-sm text-slate-400"
                  >
                    Sign out (soon)
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
