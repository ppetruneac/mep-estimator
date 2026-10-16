import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, Project } from "../api";

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
    <div className="app-shell">
      <header className="topnav" ref={navRef}>
        <div className="topnav-inner">
          <Link to="/" className="brand" onClick={() => { setProjectsOpen(false); setUserOpen(false); }}>
            <span className="brand-mark">R</span>
            <span className="brand-text">Riser</span>
          </Link>

          <nav className="topnav-links">
            <div className="menu">
              <button
                type="button"
                className={`menu-trigger ${projectsOpen ? "open" : ""}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setProjectsOpen((v) => !v);
                  setUserOpen(false);
                }}
              >
                Projects
                <span className="chevron">▾</span>
              </button>
              {projectsOpen && (
                <div className="menu-panel projects-panel">
                  <div className="menu-heading">All projects</div>
                  {projects.length === 0 && (
                    <div className="menu-empty">No projects yet</div>
                  )}
                  {projects.map((p) => (
                    <button
                      key={p.uuid}
                      type="button"
                      className="menu-item"
                      onClick={() => {
                        setProjectsOpen(false);
                        navigate(`/projects/${p.uuid}`);
                      }}
                    >
                      <div className="menu-item-title">
                        {p.title_block?.display_name || p.name}
                      </div>
                      <div className="menu-item-sub">
                        {[p.client || p.title_block?.client, p.architect || p.title_block?.architect, p.owner]
                          .filter(Boolean)
                          .join(" · ")}
                      </div>
                    </button>
                  ))}
                  <button
                    type="button"
                    className="menu-item menu-item-link"
                    onClick={() => {
                      setProjectsOpen(false);
                      navigate("/");
                    }}
                  >
                    View all projects →
                  </button>
                </div>
              )}
            </div>
          </nav>

          <div className="topnav-right">
            <div className="menu">
              <button
                type="button"
                className={`user-btn ${userOpen ? "open" : ""}`}
                aria-label="Account menu"
                onClick={(e) => {
                  e.stopPropagation();
                  setUserOpen((v) => !v);
                  setProjectsOpen(false);
                }}
              >
                <UserAvatar />
              </button>
              {userOpen && (
                <div className="menu-panel user-panel">
                  <div className="user-card">
                    <UserAvatar large />
                    <div>
                      <div className="user-name">Seneca user</div>
                      <div className="user-email">reviewer@senecagrp.com</div>
                    </div>
                  </div>
                  <div className="menu-divider" />
                  <div className="menu-heading">Organisation</div>
                  <div className="menu-static">Seneca Group Ltd</div>
                  <div className="menu-divider" />
                  <button type="button" className="menu-item" disabled>
                    Account settings (soon)
                  </button>
                  <button type="button" className="menu-item" disabled>
                    Sign out (soon)
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}

function UserAvatar({ large = false }: { large?: boolean }) {
  return (
    <span className={`avatar ${large ? "avatar-lg" : ""}`} aria-hidden>
      <svg viewBox="0 0 24 24" width="100%" height="100%" fill="none">
        <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.75" />
        <path
          d="M5 19.5c1.6-3.2 4-4.8 7-4.8s5.4 1.6 7 4.8"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
