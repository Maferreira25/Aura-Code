"use client";

import {useEffect, useState} from "react";
import catalog from "../lib/messages.json";

type Locale = keyof typeof catalog;
type MessageId = keyof (typeof catalog)["pt-BR"];
type Theme = "light" | "dark" | "contrast";

const navItems: MessageId[] = [
  "projects", "interview", "decisions", "blueprint",
  "build", "audit", "preview", "publish",
];
const proofState = "NOT_RUN";

const initialDecisions = [
  {id: "D001", topic: "Pilha e Interface", choice: "FastAPI + Next.js + PostgreSQL + Docker", status: "CONFIRMED"},
  {id: "D003", topic: "Garantia de Qualidade", choice: "Perfil AL3 (Uso Comercial com AST)", status: "CONFIRMED"},
  {id: "D004", topic: "Provedor de IA", choice: "Porta neutra compatível com API OpenAI", status: "CONFIRMED"},
  {id: "D016", topic: "Controle de Acesso", choice: "4 papéis: Proprietário, Admin, Membro, Visitante", status: "CONFIRMED"},
  {id: "D021", topic: "Exclusão e Retenção", choice: "Lixeira segura retida por 30 dias", status: "CONFIRMED"},
  {id: "D046", topic: "Arquitetura do SaaS", choice: "Monólito modular sob Clean Architecture", status: "CONFIRMED"},
  {id: "D073", topic: "Rigor de Autovalidação", choice: "Zero contornos; falhas corrigem o construtor", status: "CONFIRMED"},
  {id: "D074", topic: "Limite de Iteração", choice: "Máximo 500 linhas de diff autoral por etapa", status: "CONFIRMED"},
];

const blueprintNotebooks = [
  {num: "01", name: "PRD", desc: "Visão do produto e 74 decisões consolidadas"},
  {num: "02", name: "RULES", desc: "17 invariantes críticas e governança do construtor"},
  {num: "03", name: "ARCHITECTURE", desc: "Clean Architecture em 5 camadas e monólito modular"},
  {num: "04", name: "DATA_MODEL", desc: "Modelagem relacional PostgreSQL para o SaaS"},
  {num: "05", name: "API_SPEC", desc: "Especificação OpenAPI/REST de todos os endpoints"},
  {num: "06", name: "WORKFLOWS", desc: "Jornadas funcionais e máquinas de estados"},
  {num: "07", name: "EDGE_CASES", desc: "Concorrência, desastres e recuperação"},
  {num: "08", name: "SECURITY", desc: "Controle de acesso RBAC e contenção de IA"},
  {num: "09", name: "TEST_PLAN", desc: "Matriz APP-T01 a APP-T15 e testes de mutação"},
  {num: "10", name: "DESIGN_SYSTEM", desc: "Acessibilidade WCAG 2.2 AA e modo de contraste"},
  {num: "11", name: "TELEMETRY", desc: "Métricas abertas com opt-in e sem telemetria de código"},
  {num: "12", name: "DEPLOY", desc: "Docker Compose local e manifestos Kubernetes"},
  {num: "13", name: "DEPENDENCIES", desc: "Cadeia de suprimentos com bloqueio a pacotes novos"},
  {num: "14", name: "AGENTS", desc: "Catálogo de agentes especializados e competências"},
  {num: "15", name: "GLOSSARY", desc: "Dicionário de analogias do mundo físico para leigos"},
];

const auditChecks = [
  {key: "slop", method: "AST / check_slop_code", files: 131, status: "PASS"},
  {key: "leaks", method: "AST / check_resource_leaks", files: 131, status: "PASS"},
  {key: "sec", method: "AST / check_injection_vectors", files: 131, status: "PASS"},
  {key: "types", method: "AST / check_strict_types", files: 131, status: "PASS"},
  {key: "arch", method: "AST / check_architecture", files: 131, status: "PASS"},
  {key: "tests", method: "AST / check_test_integrity", files: 181, status: "PASS"},
  {key: "ambiguity", method: "Regex & Spec / check_ambiguity", files: 15, status: "PASS"},
  {key: "deps", method: "PyPI Index / verify_dependencies", files: 24, status: "PASS"},
  {key: "diff", method: "Unified Diff / check_surgical_diff", files: 5, status: "PASS"},
];

export default function Home() {
  const [locale, setLocale] = useState<Locale>("pt-BR");
  const [theme, setTheme] = useState<Theme>("light");
  const [activeTab, setActiveTab] = useState<MessageId>("projects");
  const [projectsList, setProjectsList] = useState<string[]>([
    "SaaS de Gestão de Projetos e Equipes",
  ]);
  const [newProjectInput, setNewProjectInput] = useState("");
  const [interviewChoice1, setInterviewChoice1] = useState("A");
  const [interviewChoice2, setInterviewChoice2] = useState("A");
  const [blueprintApproved, setBlueprintApproved] = useState(true);
  const [buildIterationRan, setBuildIterationRan] = useState(true);
  const [humanSignoff, setHumanSignoff] = useState("");
  const [releaseSealed, setReleaseSealed] = useState(false);

  const messages = catalog[locale];

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const handleAddProject = () => {
    if (newProjectInput.trim()) {
      setProjectsList([...projectsList, newProjectInput.trim()]);
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

  return (
    <div className="app" data-theme={theme}>
      <a className="skip-link" href="#content">{messages.skip}</a>
      <header className="topbar">
        <div>
          <span className="mark" aria-hidden="true">A</span>
          <strong>{messages.product}</strong>
          <span className="local-badge">{messages.local}</span>
        </div>
        <div className="preferences">
          <label>{messages.language}
            <select value={locale} onChange={(e) => setLocale(e.target.value as Locale)}>
              <option value="pt-BR">Português</option>
              <option value="en">English</option>
            </select>
          </label>
          <label>{messages.theme}
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
          <p className="eyebrow">{messages.product} / {proofState} / {messages[activeTab]}</p>
          <h1>{messages.heading}</h1>
          <p className="lead">{messages.intro}</p>

          {/* TAB 1: PROJECTS */}
          {activeTab === "projects" && (
            <section className="workflow-card">
              <h2>{messages.projects}</h2>
              <p>{messages.activeProjectLabel}: <strong>{projectsList[0]}</strong></p>
              <div className="meta-badges">
                <span className="badge primary-badge">{messages.projectGuarantee}</span>
                <span className="badge secondary-badge">{messages.projectStack}</span>
              </div>
              <div className="action-row" style={{marginTop: "1.5rem"}}>
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
              <h3 style={{marginTop: "1.5rem"}}>{messages.projectListTitle}</h3>
              <ul className="project-list">
                {projectsList.map((p, idx) => (
                  <li key={idx} className="project-item">
                    <span>{p}</span>
                    <span className="tag-ready">AL3</span>
                  </li>
                ))}
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
                <p className="analogy-text">{messages.analogyLabel} Como organizar as gavetas dos clientes no mesmo armário com chave própria.</p>
                <div className="choice-group">
                  <label className="choice-label">
                    <input
                      type="radio"
                      name="q1"
                      checked={interviewChoice1 === "A"}
                      onChange={() => setInterviewChoice1("A")}
                    />
                    Opção A: Multi-tenant isolado por tenant_id indexado (PostgreSQL)
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
                <p className="analogy-text">{messages.analogyLabel} Como a portaria do prédio confere quem pode entrar e alterar documentos na mesa.</p>
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
                  <p>{messages.noAmbiguityMsg}</p>
                </div>
              </div>
            </section>
          )}

          {/* TAB 3: DECISIONS */}
          {activeTab === "decisions" && (
            <section className="workflow-card">
              <h2>{messages.stepDecisionsTitle}</h2>
              <p className="lead-sm">{messages.stepDecisionsDesc}</p>
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
                    {initialDecisions.map((d) => (
                      <tr key={d.id}>
                        <td><code>{d.id}</code></td>
                        <td>{d.topic}</td>
                        <td>{d.choice}</td>
                        <td><span className="badge pass-badge">{d.status}</span></td>
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
                <span className="badge pass-badge">{messages.blueprintApprovedBadge}</span>
                <span className="badge secondary-badge">{messages.blueprintRevision}</span>
                <span className="badge primary-badge">{messages.notebooksCountLabel}</span>
              </div>
              <div className="notebook-grid">
                {blueprintNotebooks.map((nb) => (
                  <div key={nb.num} className="notebook-card">
                    <span className="nb-num">{nb.num}</span>
                    <div>
                      <strong>{nb.name}.md</strong>
                      <p>{nb.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="approval-box">
                <button
                  type="button"
                  className="btn primary-btn"
                  onClick={() => setBlueprintApproved(true)}
                >
                  {messages.approveBlueprintBtn}
                </button>
                {blueprintApproved && (
                  <p className="success-msg">{messages.blueprintApprovedMsg}</p>
                )}
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
                <div className="layer-item"><code>domain/</code> — Entidades puras e regras essenciais de negócio</div>
                <div className="layer-item"><code>usecases/</code> — Casos de uso e orquestração de fluxos</div>
                <div className="layer-item"><code>adapters/</code> — Controladores REST FastAPI e repositórios</div>
                <div className="layer-item"><code>infrastructure/</code> — Banco PostgreSQL, Docker e conexões</div>
                <div className="layer-item"><code>tests/</code> — Suíte automatizada com testes de mutação</div>
              </div>
              <div className="budget-box">
                <strong>{messages.budgetLabel}</strong>
                <p>195 / 500 linhas ({messages.linesLimitLabel})</p>
                <div className="progress-bar">
                  <div className="progress-fill" style={{width: "39%"}}></div>
                </div>
              </div>
              <button
                type="button"
                className="btn primary-btn"
                style={{marginTop: "1.25rem"}}
                onClick={() => setBuildIterationRan(true)}
              >
                {messages.runIterationBtn}
              </button>
              {buildIterationRan && (
                <p className="success-msg" style={{marginTop: "0.75rem"}}>
                  {messages.iterationSuccessMsg}
                </p>
              )}
            </section>
          )}

          {/* TAB 6: AUDIT */}
          {activeTab === "audit" && (
            <section className="workflow-card">
              <h2>{messages.stepAuditTitle}</h2>
              <p className="lead-sm">{messages.stepAuditDesc}</p>
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
                    {auditChecks.map((c) => (
                      <tr key={c.key}>
                        <td><strong>{c.key}</strong></td>
                        <td>{c.method}</td>
                        <td>{c.files}</td>
                        <td><span className="badge pass-badge">{messages.passBadge}</span></td>
                      </tr>
                    ))}
                    <tr>
                      <td><strong>studio_workflows</strong></td>
                      <td>Package & Journeys Inspector</td>
                      <td>8 telas</td>
                      <td><span className="badge notrun-badge">{messages.notRunBadge}</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="warning-note">{messages.noCompositeScoreWarning}</p>
            </section>
          )}

          {/* TAB 7: PREVIEW */}
          {activeTab === "preview" && (
            <section className="workflow-card">
              <h2>{messages.stepPreviewTitle}</h2>
              <p className="lead-sm">{messages.stepPreviewDesc}</p>
              <h3>{messages.serverStatusLabel}</h3>
              <div className="preview-services">
                <div className="service-row">
                  <span>FastAPI REST Server (Backend): <code>http://127.0.0.1:8000</code></span>
                  <span className="badge pass-badge">{messages.healthyBadge}</span>
                </div>
                <div className="service-row">
                  <span>PostgreSQL Database: <code>127.0.0.1:5432</code></span>
                  <span className="badge pass-badge">{messages.healthyBadge}</span>
                </div>
                <div className="service-row">
                  <span>Next.js Web Showcase: <code>http://127.0.0.1:3000</code></span>
                  <span className="badge pass-badge">{messages.healthyBadge}</span>
                </div>
              </div>
              <button type="button" className="btn secondary-btn" style={{marginTop: "1.5rem"}}>
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
                <li><span className="check-box checked" aria-hidden="true">✓</span> {messages.checkItem1}</li>
                <li><span className="check-box checked" aria-hidden="true">✓</span> {messages.checkItem2}</li>
                <li><span className="check-box checked" aria-hidden="true">✓</span> {messages.checkItem3}</li>
                <li><span className="check-box checked" aria-hidden="true">✓</span> {messages.checkItem4}</li>
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
                  style={{marginTop: "1rem"}}
                >
                  {messages.signAndPublishBtn}
                </button>
                {releaseSealed && (
                  <p className="success-msg" style={{marginTop: "0.75rem"}}>
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

          <details style={{marginTop: "2rem"}}>
            <summary>{messages.details}</summary>
            <code>{proofState}: studio-runtime (AuraCode v0.3.0.dev0)</code>
          </details>
        </main>
      </div>
    </div>
  );
}
