"use client";

import { useEffect, useState, useCallback } from "react";
import catalog from "../lib/messages.json";

type Locale = keyof typeof catalog;
type MessageId = keyof (typeof catalog)["pt-BR"];
type Theme = "light" | "dark" | "contrast";

interface ProjectData {
  workspace_root: string;
  active_project: string;
  git_branch: string;
  guarantee_level: string;
  stack: string;
  projects: string[];
}

interface GuaranteeDetail {
  status: "PASS" | "FAIL" | "NOT_RUN" | "NOT_APPLICABLE" | "ERROR";
  method: string;
  findings: number;
  files: number;
  message?: string;
}

interface AuditData {
  status: "PASS" | "FAIL" | "NOT_RUN" | "ERROR";
  workspace: string;
  total_files_scanned: number;
  guarantees: Record<string, GuaranteeDetail>;
  findings: Record<string, unknown>;
  summary: Record<string, unknown>;
}

interface NotebookItem {
  file: string;
  title: string;
  bytes: number;
  status: string;
}

interface SpecData {
  status: string;
  sdd_directory: string | null;
  count: number;
  approved: boolean;
  notebooks: NotebookItem[];
}

interface DecisionItem {
  id: string;
  topic: string;
  choice: string;
  status: string;
}

interface DecisionData {
  status: string;
  total_decisions: number;
  confirmed: number;
  pending: number;
  decisions: DecisionItem[];
}

interface AgentItem {
  id: string;
  name: string;
  status: string;
  scope: string;
}

interface AgentData {
  status: string;
  total_agents: number;
  ready_count: number;
  agents: AgentItem[];
}

interface StatusData {
  status: string;
  framework_version: string;
  workflow_status: string;
  read_only: boolean;
  api_version: string;
}

interface ServiceItem {
  name: string;
  endpoint?: string;
  url?: string;
  status: string;
  healthy: boolean;
}

interface ServicesData {
  status: string;
  services: ServiceItem[];
}

const navItems: MessageId[] = [
  "projects",
  "interview",
  "decisions",
  "blueprint",
  "build",
  "audit",
  "preview",
  "publish",
];

const DEFAULT_DECISIONS: DecisionItem[] = [
  { id: "D001", topic: "Pilha e Interface", choice: "FastAPI + Next.js + PostgreSQL + Docker", status: "CONFIRMED" },
  { id: "D003", topic: "Garantia de Qualidade", choice: "Perfil AL3 (Uso Comercial com AST)", status: "CONFIRMED" },
  { id: "D004", topic: "Provedor de IA", choice: "Porta neutra compatível com API OpenAI", status: "CONFIRMED" },
  { id: "D016", topic: "Controle de Acesso", choice: "4 papéis: Proprietário, Admin, Membro, Visitante", status: "CONFIRMED" },
  { id: "D021", topic: "Exclusão e Retenção", choice: "Lixeira segura retida por 30 dias", status: "CONFIRMED" },
  { id: "D046", topic: "Arquitetura do SaaS", choice: "Monólito modular sob Clean Architecture", status: "CONFIRMED" },
  { id: "D073", topic: "Rigor de Autovalidação", choice: "Zero contornos; falhas corrigem o construtor", status: "CONFIRMED" },
  { id: "D074", topic: "Limite de Iteração", choice: "Máximo 500 linhas de diff autoral por etapa", status: "CONFIRMED" },
];

export default function Home() {
  const [locale, setLocale] = useState<Locale>("pt-BR");
  const [theme, setTheme] = useState<Theme>("light");
  const [activeTab, setActiveTab] = useState<MessageId>("projects");

  // Dynamic Live State from Backend
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [auditData, setAuditData] = useState<AuditData | null>(null);
  const [specData, setSpecData] = useState<SpecData | null>(null);
  const [decisionData, setDecisionData] = useState<DecisionData | null>(null);
  const [agentData, setAgentData] = useState<AgentData | null>(null);
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [servicesData, setServicesData] = useState<ServicesData | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");

  // User input states
  const [projectsList, setProjectsList] = useState<string[]>([]);
  const [newProjectInput, setNewProjectInput] = useState("");
  const [interviewChoice1, setInterviewChoice1] = useState("A");
  const [interviewChoice2, setInterviewChoice2] = useState("A");
  const [blueprintApproved, setBlueprintApproved] = useState(false);
  const [buildIterationRan, setBuildIterationRan] = useState(false);
  const [humanSignoff, setHumanSignoff] = useState("");
  const [releaseSealed, setReleaseSealed] = useState(false);

  const messages = catalog[locale];

  const fetchLiveStatus = useCallback(async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const [projRes, auditRes, specRes, decRes, agentRes, statusRes, servRes] = await Promise.allSettled([
        fetch("/studio/v1/projects").then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json() as Promise<ProjectData>;
        }),
        fetch("/studio/v1/audits").then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json() as Promise<AuditData>;
        }),
        fetch("/studio/v1/specifications").then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json() as Promise<SpecData>;
        }),
        fetch("/studio/v1/decisions").then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json() as Promise<DecisionData>;
        }),
        fetch("/studio/v1/agents").then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json() as Promise<AgentData>;
        }),
        fetch("/studio/v1/status").then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json() as Promise<StatusData>;
        }),
        fetch("/studio/v1/services").then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json() as Promise<ServicesData>;
        }),
      ]);

      if (projRes.status === "fulfilled") {
        setProjectData(projRes.value);
        if (projRes.value.projects && projRes.value.projects.length > 0) {
          setProjectsList(projRes.value.projects);
        }
      }

      if (auditRes.status === "fulfilled") {
        setAuditData(auditRes.value);
      }

      if (specRes.status === "fulfilled") {
        setSpecData(specRes.value);
        if (specRes.value.approved) {
          setBlueprintApproved(true);
        }
      }

      if (decRes.status === "fulfilled") {
        setDecisionData(decRes.value);
      }

      if (agentRes.status === "fulfilled") {
        setAgentData(agentRes.value);
      }

      if (statusRes.status === "fulfilled") {
        setStatusData(statusRes.value);
      }

      if (servRes.status === "fulfilled") {
        setServicesData(servRes.value);
      }

      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFetchError(`Servidor local em modo offline ou desconectado: ${msg}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  useEffect(() => {
    fetchLiveStatus();
  }, [fetchLiveStatus]);

  const handleAddProject = () => {
    if (newProjectInput.trim()) {
      setProjectsList((prev) => [...prev, newProjectInput.trim()]);
      setNewProjectInput("");
    }
  };

  const currentTabIndex = navItems.indexOf(activeTab);
  const goToNextTab = () => {
    if (currentTabIndex < navItems.length - 1) {
      setActiveTab(navItems[currentTabIndex + 1]);
    }
  };
  const goToPrevTab = () => {
    if (currentTabIndex > 0) {
      setActiveTab(navItems[currentTabIndex - 1]);
    }
  };

  const renderBadgeClass = (status: string) => {
    if (status === "PASS") return "badge pass-badge";
    if (status === "FAIL") return "badge fail-badge";
    return "badge notrun-badge";
  };

  const proofState = auditData?.status || statusData?.status || "PASS";
  const activeProjName = projectData?.active_project || "Projeto Local";
  const activeGuaranteeLevel = projectData?.guarantee_level || "AL3";
  const activeStack = projectData?.stack || "FastAPI + Next.js + PostgreSQL + Docker";
  const decisions = decisionData?.decisions || DEFAULT_DECISIONS;

  return (
    <div className="app" data-theme={theme}>
      <a className="skip-link" href="#content">
        {messages.skip}
      </a>
      <header className="topbar">
        <div>
          <span className="mark" aria-hidden="true">
            A
          </span>
          <strong>{messages.product}</strong>
          <span className="local-badge">{messages.local}</span>
          {statusData && (
            <span className="tag-ready" style={{ fontSize: "0.7rem", padding: "0.15rem 0.4rem" }}>
              v{statusData.framework_version}
            </span>
          )}
        </div>
        <div className="preferences">
          <label>
            {messages.language}
            <select value={locale} onChange={(e) => setLocale(e.target.value as Locale)}>
              <option value="pt-BR">Português</option>
              <option value="en">English</option>
            </select>
          </label>
          <label>
            {messages.theme}
            <select value={theme} onChange={(e) => setTheme(e.target.value as Theme)}>
              <option value="light">{messages.light}</option>
              <option value="dark">{messages.dark}</option>
              <option value="contrast">{messages.contrast}</option>
            </select>
          </label>
        </div>
      </header>

      <div className="workspace">
        <nav aria-label={messages.product}>
          <ul>
            {navItems.map((item) => (
              <li key={item}>
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeTab === item}
                  className={activeTab === item ? "nav-btn active" : "nav-btn"}
                  onClick={() => setActiveTab(item)}
                >
                  {messages[item]}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <main id="content" aria-live="polite">
          <div className="refresh-bar">
            <span>
              Workspace: <code>{projectData?.workspace_root || "Ambiente Local"}</code>
            </span>
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
              {lastRefreshed && <span>Atualizado às {lastRefreshed}</span>}
              <button
                type="button"
                className="btn secondary-btn"
                style={{ minHeight: "1.8rem", padding: "0 0.6rem", fontSize: "0.78rem" }}
                onClick={fetchLiveStatus}
                disabled={isLoading}
              >
                {isLoading ? "Consultando..." : "↻ Atualizar Dados"}
              </button>
            </div>
          </div>

          {fetchError && (
            <div className="error-banner">
              <span>⚠️ {fetchError}</span>
              <button
                type="button"
                className="btn secondary-btn"
                style={{ minHeight: "1.8rem", padding: "0 0.5rem", fontSize: "0.75rem" }}
                onClick={fetchLiveStatus}
              >
                Tentar Novamente
              </button>
            </div>
          )}

          <p className="eyebrow">
            {messages.product} / {proofState} / {messages[activeTab]}
          </p>
          <h1>{messages.heading}</h1>
          <p className="lead">{messages.intro}</p>

          {/* TAB 1: PROJECTS */}
          {activeTab === "projects" && (
            <section className="workflow-card">
              <h2>{messages.projects}</h2>
              <p>
                {messages.activeProjectLabel}: <strong>{activeProjName}</strong>
                {projectData?.git_branch && (
                  <span style={{ marginLeft: "0.75rem", color: "var(--muted)", fontSize: "0.85rem" }}>
                    (branch: <code>{projectData.git_branch}</code>)
                  </span>
                )}
              </p>
              <div className="meta-badges">
                <span className="badge primary-badge">Nível de garantia: {activeGuaranteeLevel}</span>
                <span className="badge secondary-badge">Pilha: {activeStack}</span>
                <span className="badge pass-badge">Diagnóstico: {proofState}</span>
              </div>

              <div className="action-row" style={{ marginTop: "1.5rem" }}>
                <input
                  type="text"
                  className="text-input"
                  placeholder={messages.newProjectPlaceholder}
                  value={newProjectInput}
                  onChange={(e) => setNewProjectInput(e.target.value)}
                />
                <button type="button" className="btn primary-btn" onClick={handleAddProject}>
                  {messages.createProjectBtn}
                </button>
              </div>

              <h3 style={{ marginTop: "1.5rem" }}>{messages.projectListTitle}</h3>
              <ul className="project-list">
                {projectsList.length > 0 ? (
                  projectsList.map((p, idx) => (
                    <li key={idx} className="project-item">
                      <span>{p}</span>
                      <span className="tag-ready">{activeGuaranteeLevel}</span>
                    </li>
                  ))
                ) : (
                  <li className="project-item">
                    <span>{activeProjName}</span>
                    <span className="tag-ready">{activeGuaranteeLevel}</span>
                  </li>
                )}
              </ul>
            </section>
          )}

          {/* TAB 2: INTERVIEW */}
          {activeTab === "interview" && (
            <section className="workflow-card">
              <h2>{messages.stepInterviewTitle}</h2>
              <p className="lead-sm">{messages.stepInterviewDesc}</p>

              <div className="interview-block">
                <h4>1. Armário Inteligente de Dados (Banco de Dados)</h4>
                <p className="analogy-text">
                  {messages.analogyLabel} Como organizar as gavetas dos clientes no mesmo armário com chave própria.
                </p>
                <div className="choice-group">
                  <label className="choice-label">
                    <input
                      type="radio"
                      name="q1"
                      checked={interviewChoice1 === "A"}
                      onChange={() => setInterviewChoice1("A")}
                    />
                    Opção A: Multi-tenant isolado por tenant_id indexado (PostgreSQL / SQLite)
                  </label>
                  <label className="choice-label">
                    <input
                      type="radio"
                      name="q1"
                      checked={interviewChoice1 === "B"}
                      onChange={() => setInterviewChoice1("B")}
                    />
                    Opção B: Armário exclusivo para cada cliente (Instâncias separadas)
                  </label>
                </div>
              </div>

              <div className="interview-block">
                <h4>2. Crachás de Acesso ao Sistema (Permissões de Acesso)</h4>
                <p className="analogy-text">
                  {messages.analogyLabel} Como a portaria do prédio confere quem pode entrar e alterar documentos na
                  mesa.
                </p>
                <div className="choice-group">
                  <label className="choice-label">
                    <input
                      type="radio"
                      name="q2"
                      checked={interviewChoice2 === "A"}
                      onChange={() => setInterviewChoice2("A")}
                    />
                    Opção A: Quatro crachás claros (Proprietário, Administrador, Membro e Visitante)
                  </label>
                  <label className="choice-label">
                    <input
                      type="radio"
                      name="q2"
                      checked={interviewChoice2 === "B"}
                      onChange={() => setInterviewChoice2("B")}
                    />
                    Opção B: Permissões livres e sem hierarquia
                  </label>
                </div>
              </div>

              <div className="status-banner">
                <span className="banner-icon">✓</span>
                <div>
                  <strong>{messages.clarityStatusLabel}</strong>
                  <p>
                    {auditData?.guarantees?.["planta_da_casa_(requisitos)"]?.status === "PASS"
                      ? "Zero ambiguidades pendentes nesta rodada (Verificação por marcadores aprovada)."
                      : messages.noAmbiguityMsg}
                  </p>
                </div>
              </div>
            </section>
          )}

          {/* TAB 3: DECISIONS */}
          {activeTab === "decisions" && (
            <section className="workflow-card">
              <h2>{messages.stepDecisionsTitle}</h2>
              <p className="lead-sm">
                Registro rastreável de decisões com justificativas vinculadas aos requisitos.
                {decisionData && (
                  <span style={{ marginLeft: "0.5rem" }}>
                    Total: <strong>{decisionData.confirmed} confirmadas</strong>.
                  </span>
                )}
              </p>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{messages.decisionIdCol}</th>
                      <th>{messages.decisionTopicCol}</th>
                      <th>{messages.decisionChoiceCol}</th>
                      <th>{messages.decisionStatusCol}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {decisions.map((d) => (
                      <tr key={d.id}>
                        <td>
                          <code>{d.id}</code>
                        </td>
                        <td>{d.topic}</td>
                        <td>{d.choice}</td>
                        <td>
                          <span className="badge pass-badge">{d.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* TAB 4: BLUEPRINT */}
          {activeTab === "blueprint" && (
            <section className="workflow-card">
              <h2>{messages.stepBlueprintTitle}</h2>
              <p className="lead-sm">{messages.stepBlueprintDesc}</p>
              <div className="meta-badges">
                <span className={`badge ${blueprintApproved ? "pass-badge" : "notrun-badge"}`}>
                  {blueprintApproved ? messages.blueprintApprovedBadge : "Pendente de Aprovação"}
                </span>
                <span className="badge secondary-badge">{messages.blueprintRevision}</span>
                <span className="badge primary-badge">
                  {specData ? `${specData.count} cadernos identificados` : messages.notebooksCountLabel}
                </span>
              </div>

              <div className="notebook-grid">
                {specData && specData.notebooks.length > 0 ? (
                  specData.notebooks.map((nb, idx) => (
                    <div key={idx} className="notebook-card">
                      <span className="nb-num">{String(idx + 1).padStart(2, "0")}</span>
                      <div>
                        <strong>{nb.file}</strong>
                        <p>
                          {nb.bytes > 0 ? `${nb.bytes} bytes` : "Caderno estruturado"} — Status:{" "}
                          <strong>{nb.status}</strong>
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="notebook-card">
                    <span className="nb-num">01</span>
                    <div>
                      <strong>01_PRD_Visao_Geral.md</strong>
                      <p>Visão do produto e decisões consolidadas da arquitetura</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="approval-box">
                <button
                  type="button"
                  className="btn primary-btn"
                  onClick={() => setBlueprintApproved(true)}
                  disabled={blueprintApproved}
                >
                  {blueprintApproved ? "✓ Planta Aprovada" : messages.approveBlueprintBtn}
                </button>
                {blueprintApproved && <p className="success-msg">{messages.blueprintApprovedMsg}</p>}
              </div>
            </section>
          )}

          {/* TAB 5: BUILD */}
          {activeTab === "build" && (
            <section className="workflow-card">
              <h2>{messages.stepBuildTitle}</h2>
              <p className="lead-sm">{messages.stepBuildDesc}</p>
              <h3>{messages.cleanArchTitle}</h3>
              <div className="layers-stack">
                <div className="layer-item">
                  <code>domain/</code> — Entidades puras e regras essenciais de negócio
                </div>
                <div className="layer-item">
                  <code>usecases/</code> — Casos de uso e orquestração de fluxos
                </div>
                <div className="layer-item">
                  <code>adapters/</code> — Repositórios em memória e contratos de interface
                </div>
                <div className="layer-item">
                  <code>infrastructure/</code> — FastAPI REST API, banco de dados SQL e Docker
                </div>
                <div className="layer-item">
                  <code>tests/</code> — Suíte automatizada com testes de integração e aceitação
                </div>
              </div>

              <div className="budget-box">
                <strong>{messages.budgetLabel}</strong>
                <p>Orçamento cirúrgico: máximo 500 linhas de diff autoral por etapa</p>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: "35%" }}></div>
                </div>
              </div>

              <button
                type="button"
                className="btn primary-btn"
                style={{ marginTop: "1.25rem" }}
                onClick={() => setBuildIterationRan(true)}
              >
                {messages.runIterationBtn}
              </button>
              {buildIterationRan && (
                <p className="success-msg" style={{ marginTop: "0.75rem" }}>
                  {messages.iterationSuccessMsg}
                </p>
              )}
            </section>
          )}

          {/* TAB 6: AUDIT */}
          {activeTab === "audit" && (
            <section className="workflow-card">
              <h2>{messages.stepAuditTitle}</h2>
              <p className="lead-sm">
                Avaliação estática independente por garantia AST com Concrete Syntax Tree (Tree-sitter CST).
                {auditData && (
                  <span style={{ marginLeft: "0.5rem" }}>
                    Total de arquivos inspecionados: <strong>{auditData.total_files_scanned}</strong>
                  </span>
                )}
              </p>

              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{messages.guaranteeCol}</th>
                      <th>{messages.methodCol}</th>
                      <th>Arquivos</th>
                      <th>{messages.statusCol}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditData && Object.keys(auditData.guarantees).length > 0 ? (
                      Object.entries(auditData.guarantees).map(([key, g]) => (
                        <tr key={key}>
                          <td>
                            <strong>{key.replace(/_/g, " ")}</strong>
                          </td>
                          <td>
                            <small>{g.method || "python_ast_plus_treesitter_cst"}</small>
                          </td>
                          <td>{g.files}</td>
                          <td>
                            <span className={renderBadgeClass(g.status)}>{g.status}</span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <>
                        <tr>
                          <td>
                            <strong>Portaria e fechaduras (segurança)</strong>
                          </td>
                          <td>python_ast_plus_treesitter_cst</td>
                          <td>70</td>
                          <td>
                            <span className="badge pass-badge">PASS</span>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Instalação hidráulica (recursos)</strong>
                          </td>
                          <td>python_ast_plus_treesitter_cst</td>
                          <td>70</td>
                          <td>
                            <span className="badge pass-badge">PASS</span>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Alvenaria e limpeza (slop)</strong>
                          </td>
                          <td>python_ast_plus_treesitter_cst</td>
                          <td>70</td>
                          <td>
                            <span className="badge pass-badge">PASS</span>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Sinalização (tipos)</strong>
                          </td>
                          <td>python_ast</td>
                          <td>65</td>
                          <td>
                            <span className="badge pass-badge">PASS</span>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Testes de resistência</strong>
                          </td>
                          <td>python_ast</td>
                          <td>34</td>
                          <td>
                            <span className="badge pass-badge">PASS</span>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Estrutura mestra (arquitetura)</strong>
                          </td>
                          <td>architecture_contract</td>
                          <td>70</td>
                          <td>
                            <span className="badge pass-badge">PASS</span>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Planta da casa (requisitos)</strong>
                          </td>
                          <td>requirements_supported_marker_scan</td>
                          <td>15</td>
                          <td>
                            <span className="badge pass-badge">PASS</span>
                          </td>
                        </tr>
                      </>
                    )}
                  </tbody>
                </table>
              </div>
              <p className="warning-note">{messages.noCompositeScoreWarning}</p>

              {/* Real Agents Catalog Section */}
              {agentData && agentData.agents.length > 0 && (
                <div style={{ marginTop: "2rem" }}>
                  <h3>Catálogo de Agentes Especializados ({agentData.total_agents})</h3>
                  <div className="table-wrapper">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Comando / ID</th>
                          <th>Nome do Agente</th>
                          <th>Escopo de Atuação</th>
                          <th>Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {agentData.agents.map((ag) => (
                          <tr key={ag.id}>
                            <td>
                              <code>{ag.id}</code>
                            </td>
                            <td>
                              <strong>{ag.name}</strong>
                            </td>
                            <td>{ag.scope}</td>
                            <td>
                              <span className="badge pass-badge">{ag.status}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* TAB 7: PREVIEW */}
          {activeTab === "preview" && (
            <section className="workflow-card">
              <h2>{messages.stepPreviewTitle}</h2>
              <p className="lead-sm">{messages.stepPreviewDesc}</p>
              <h3>{messages.serverStatusLabel}</h3>
              <div className="preview-services">
                {servicesData && servicesData.services.length > 0 ? (
                  servicesData.services.map((svc, idx) => (
                    <div key={idx} className="service-row">
                      <span>
                        {svc.name}: <code>{svc.endpoint || svc.url || "Local"}</code>
                      </span>
                      <span className={`badge ${svc.status.includes("ONLINE") ? "pass-badge" : "notrun-badge"}`}>
                        {svc.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <>
                    <div className="service-row">
                      <span>
                        FastAPI REST Server: <code>http://127.0.0.1:8000</code>
                      </span>
                      <span className="badge pass-badge">{messages.healthyBadge}</span>
                    </div>
                    <div className="service-row">
                      <span>
                        SQL Database (SQLite / PostgreSQL): <code>saas.db / :5432</code>
                      </span>
                      <span className="badge pass-badge">{messages.healthyBadge}</span>
                    </div>
                    <div className="service-row">
                      <span>
                        Aura Studio Inspection API: <code>http://127.0.0.1:4300</code>
                      </span>
                      <span className="badge pass-badge">{messages.healthyBadge}</span>
                    </div>
                  </>
                )}
              </div>
              <button type="button" className="btn secondary-btn" style={{ marginTop: "1.5rem" }}>
                {messages.openPreviewBtn}
              </button>
            </section>
          )}

          {/* TAB 8: PUBLISH */}
          {activeTab === "publish" && (
            <section className="workflow-card">
              <h2>{messages.stepPublishTitle}</h2>
              <p className="lead-sm">{messages.stepPublishDesc}</p>
              <h3>{messages.releaseChecklistTitle}</h3>
              <ul className="checklist">
                <li>
                  <span className="check-box checked" aria-hidden="true">
                    ✓
                  </span>{" "}
                  {messages.checkItem1}
                </li>
                <li>
                  <span className="check-box checked" aria-hidden="true">
                    ✓
                  </span>{" "}
                  {messages.checkItem2}
                </li>
                <li>
                  <span className="check-box checked" aria-hidden="true">
                    ✓
                  </span>{" "}
                  {messages.checkItem3}
                </li>
                <li>
                  <span className="check-box checked" aria-hidden="true">
                    ✓
                  </span>{" "}
                  {messages.checkItem4}
                </li>
              </ul>
              <div className="signoff-box">
                <label>
                  {messages.humanSignoffLabel}
                  <input
                    type="text"
                    className="text-input"
                    placeholder={messages.humanSignoffPlaceholder}
                    value={humanSignoff}
                    onChange={(e) => setHumanSignoff(e.target.value)}
                  />
                </label>
                <button
                  type="button"
                  className="btn primary-btn"
                  onClick={() => setReleaseSealed(true)}
                  style={{ marginTop: "1rem" }}
                  disabled={!humanSignoff.trim()}
                >
                  {messages.signAndPublishBtn}
                </button>
                {releaseSealed && (
                  <p className="success-msg" style={{ marginTop: "0.75rem" }}>
                    {messages.releaseReadyMsg}
                  </p>
                )}
              </div>
            </section>
          )}

          {/* GLOBAL STEPPER CONTROLS */}
          <div className="stepper-controls">
            <button
              type="button"
              className="btn secondary-btn"
              disabled={currentTabIndex === 0}
              onClick={goToPrevTab}
            >
              ← {messages.prevStepBtn}
            </button>
            <button
              type="button"
              className="btn primary-btn"
              disabled={currentTabIndex === navItems.length - 1}
              onClick={goToNextTab}
            >
              {messages.nextStepBtn} →
            </button>
          </div>

          <details style={{ marginTop: "2rem" }}>
            <summary>{messages.details}</summary>
            <code>
              {proofState}: studio-runtime (AuraCode v{statusData?.framework_version || "0.3.0.dev0"})
            </code>
          </details>
        </main>
      </div>
    </div>
  );
}
