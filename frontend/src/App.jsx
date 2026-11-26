import { useEffect, useState } from "react";
import {
  BookOpen, FileText, Upload, Search, Sparkles, ChevronDown,
  ExternalLink, LoaderCircle, Network, GitBranch, RefreshCw,
  FileSearch, AlertCircle, CheckCircle2,Lightbulb, Compass, 
  WandSparkles, FileCheck2, MessageCircleQuestion, ClipboardList,
  ShieldCheck, Swords, Scale, Gauge, Cpu, Wallet, Accessibility, Bot, Workflow, Play, History, FolderKanban, Plus, Download, Trash2,
} from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:8001";

function ReviewBulletList({ title, items }) {
  if (!items?.length) return null;
  return (
    <div className="review-bullet-list">
      <strong>{title}</strong>
      <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul>
    </div>
  );
}

function formatRealityValue(value) {
  if (value === null || value === undefined) {
    return "Not specified";
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return "None listed";

    return value
      .map((item) =>
        typeof item === "object"
          ? JSON.stringify(item, null, 2)
          : String(item)
      )
      .join("\n");
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function RealityDetail({ title, data }) {
  if (!data || typeof data !== "object") return null;

  return (
    <section className="reality-result-section">
      <h3>{title}</h3>

      <div className="reality-detail-grid">
        {Object.entries(data).map(([key, value]) => (
          <div className="reality-detail-item" key={key}>
            <strong>
              {key.replaceAll("_", " ")}
            </strong>

            <pre>{formatRealityValue(value)}</pre>
          </div>
        ))}
      </div>
    </section>
  );
}

function App() {
  const [papers, setPapers] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [askError, setAskError] = useState("");
  const [activeView, setActiveView] = useState("ask");
  const [claims, setClaims] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [claimLoading, setClaimLoading] = useState(false);
  const [relationshipLoading, setRelationshipLoading] = useState(false);
  const [claimMessage, setClaimMessage] = useState("");
  const [claimError, setClaimError] = useState("");

  const [insights, setInsights] = useState([]);
  const [insightLoading, setInsightLoading] = useState(false);
  const [insightError, setInsightError] = useState("");
  const [insightMessage, setInsightMessage] = useState("");
  const [insightType, setInsightType] = useState("blind_spot");

  // Phase 3: Future Reviewer
  const [reviewForm, setReviewForm] = useState({
    research_title: "",
    research_idea: "",
    proposed_methodology: "",
    proposed_dataset: "",
    proposed_metrics: "",
  });
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const [reviewMessage, setReviewMessage] = useState("");
  const [reviews, setReviews] = useState([]);
  const [selectedReview, setSelectedReview] = useState(null);
  const [reviewsLoading, setReviewsLoading] = useState(false);

  // Phase 4: Research Debate
  const [debates, setDebates] = useState([]);
  const [selectedDebate, setSelectedDebate] = useState(null);
  const [debateReviewId, setDebateReviewId] = useState("");
  const [debateLoading, setDebateLoading] = useState(false);
  const [debateError, setDebateError] = useState("");
  const [debateMessage, setDebateMessage] = useState("");
  const [debatesLoading, setDebatesLoading] = useState(false);

  const loadPapers = async () => {
    const response = await fetch(`${API}/papers`);
    if (!response.ok) throw new Error("Failed to load papers.");
    const data = await response.json();
    setPapers(data.papers || []);
  };

  const loadClaimsAndGraph = async () => {
    // The graph must include all papers; otherwise cross-paper relationships
    // disappear whenever a single paper is selected for extraction.
    const [claimResponse, graphResponse] = await Promise.all([
      fetch(`${API}/claims`),
      fetch(`${API}/claims/graph`)
    ]);
    if (!claimResponse.ok || !graphResponse.ok) {
      throw new Error("Could not load claims or graph. Check PostgreSQL and the backend.");
    }
    const claimData = await claimResponse.json();
    const graphData = await graphResponse.json();
    setClaims(claimData.claims || []);
    setGraph(graphData || { nodes: [], edges: [] });
  };

  // Phase 5: Research Reality Simulator
  const [realityAssessments, setRealityAssessments] = useState([]);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [realityReviewId, setRealityReviewId] = useState("");

  const [realityLoading, setRealityLoading] = useState(false);
  const [realityHistoryLoading, setRealityHistoryLoading] = useState(false);

  const [realityError, setRealityError] = useState("");
  const [realityMessage, setRealityMessage] = useState("");

  // Phase 6: Agentic Research Workflow
  const [workflowRequest, setWorkflowRequest] = useState("");
  const [workflowReviewId, setWorkflowReviewId] = useState("");
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [workflowHistory, setWorkflowHistory] = useState([]);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [workflowHistoryLoading, setWorkflowHistoryLoading] = useState(false);
  const [workflowError, setWorkflowError] = useState("");
  const [workflowMessage, setWorkflowMessage] = useState("");

  // Phase 7: Research Workspace & Report Generation
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [workspaceReports, setWorkspaceReports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [workspaceForm, setWorkspaceForm] = useState({ title: "", description: "", research_question: "", paper_ids: [] });
  const [workspaceLoading, setWorkspaceLoading] = useState(false);
  const [workspaceError, setWorkspaceError] = useState("");
  const [workspaceMessage, setWorkspaceMessage] = useState("");


  useEffect(() => {
    loadPapers().catch((error) => setUploadError(error.message));
  }, []);

  useEffect(() => {
    if (activeView === "claims") {
      loadClaimsAndGraph().catch((error) => setClaimError(error.message));
    }
  }, [activeView, selectedPaper]);

  useEffect(() => {
    if (activeView === "intelligence") {
      loadInsights().catch((error) => {
        setInsightError(error.message);
      });
    }
    if (activeView === "reviewer") {
      loadReviews().catch((error) => setReviewError(error.message));
    }
    if (activeView === "debate") {
      loadReviews().catch((error) => setDebateError(error.message));
      loadDebates().catch((error) => setDebateError(error.message));
    }
    if (activeView === "reality") {
      loadReviews().catch((error) => setRealityError(error.message));
      loadRealityAssessments().catch((error) => setRealityError(error.message));
    }
    if (activeView === "workflow") {
      loadReviews().catch((error) => setWorkflowError(error.message));
      loadWorkflowHistory().catch((error) => setWorkflowError(error.message));
    }
    if (activeView === "workspace") {
      loadWorkspaces().catch((error) => setWorkspaceError(error.message));
    }
  }, [activeView]);

  // Phase 6: Agentic Research Workflow API actions
  const loadWorkflowHistory = async () => {
    setWorkflowHistoryLoading(true);
    try {
      const response = await fetch(`${API}/agentic-workflows`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to load workflow history.");
      setWorkflowHistory(data.workflows || []);
    } finally {
      setWorkflowHistoryLoading(false);
    }
  };

  const runAgenticWorkflow = async (event) => {
    event.preventDefault();
    if (workflowRequest.trim().length < 10) {
      setWorkflowError("Please describe your research task in at least 10 characters.");
      return;
    }
    setWorkflowLoading(true);
    setWorkflowError("");
    setWorkflowMessage("");
    setSelectedWorkflow(null);
    try {
      const response = await fetch(`${API}/agentic-workflows/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request: workflowRequest.trim(),
          future_review_id: workflowReviewId || null,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Agentic workflow failed.");
      setSelectedWorkflow(data);
      setWorkflowMessage("Workflow execution finished. Review the plan and each tool result below.");
      await loadWorkflowHistory();
    } catch (error) {
      setWorkflowError(error.message || "Unable to execute the workflow.");
    } finally {
      setWorkflowLoading(false);
    }
  };

  const openPreviousWorkflow = async (workflowId) => {
    setWorkflowError("");
    try {
      const response = await fetch(`${API}/agentic-workflows/${encodeURIComponent(workflowId)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to open workflow.");
      setSelectedWorkflow(data);
      setWorkflowRequest(data.user_request || "");
      setWorkflowReviewId(data.future_review_id || "");
    } catch (error) {
      setWorkflowError(error.message || "Unable to open workflow.");
    }
  };

  // Phase 7 API actions
  const loadWorkspaces = async () => {
    const response = await fetch(`${API}/research-workspaces`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Unable to load workspaces.");
    setWorkspaces(data.workspaces || []);
  };

  const createWorkspace = async (event) => {
    event.preventDefault(); setWorkspaceLoading(true); setWorkspaceError(""); setWorkspaceMessage("");
    try {
      const response = await fetch(`${API}/research-workspaces`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(workspaceForm) });
      const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Unable to create workspace.");
      setActiveWorkspace(data); setWorkspaceForm({ title: "", description: "", research_question: "", paper_ids: [] });
      setWorkspaceMessage("Research workspace created."); await loadWorkspaces(); await loadWorkspaceReports(data.id);
    } catch (error) { setWorkspaceError(error.message); } finally { setWorkspaceLoading(false); }
  };

  const openWorkspace = async (id) => {
    setWorkspaceError(""); setActiveReport(null);
    try { const response = await fetch(`${API}/research-workspaces/${encodeURIComponent(id)}`); const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to open workspace."); setActiveWorkspace(data);
      setWorkspaceForm({ title: data.title, description: data.description || "", research_question: data.research_question || "", paper_ids: data.paper_ids || [] }); await loadWorkspaceReports(id);
    } catch (error) { setWorkspaceError(error.message); }
  };

  const loadWorkspaceReports = async (id) => {
    const response = await fetch(`${API}/research-workspaces/${encodeURIComponent(id)}/reports`); const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Unable to load reports."); setWorkspaceReports(data.reports || []);
  };

  const saveWorkspace = async (event) => {
    event.preventDefault(); if (!activeWorkspace) return; setWorkspaceLoading(true); setWorkspaceError("");
    try { const response = await fetch(`${API}/research-workspaces/${activeWorkspace.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(workspaceForm) });
      const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Unable to save workspace."); setActiveWorkspace(data); setWorkspaceMessage("Workspace updated."); await loadWorkspaces();
    } catch (error) { setWorkspaceError(error.message); } finally { setWorkspaceLoading(false); }
  };

  const generateWorkspaceReport = async () => {
    if (!activeWorkspace) return; setWorkspaceLoading(true); setWorkspaceError(""); setWorkspaceMessage("");
    try { const response = await fetch(`${API}/research-workspaces/${activeWorkspace.id}/reports/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ include_claims: true, include_insights: true, include_reviews: true, include_workflows: true }) });
      const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Report generation failed."); setActiveReport(data); setWorkspaceMessage("Report generated and saved."); await loadWorkspaceReports(activeWorkspace.id); await loadWorkspaces();
    } catch (error) { setWorkspaceError(error.message); } finally { setWorkspaceLoading(false); }
  };

  const openReport = async (id) => {
    try { const response = await fetch(`${API}/research-reports/${encodeURIComponent(id)}`); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Unable to open report."); setActiveReport(data); }
    catch (error) { setWorkspaceError(error.message); }
  };

  const deleteWorkspace = async () => {
    if (!activeWorkspace || !window.confirm("Delete this workspace and all its saved reports?")) return;
    try { const response = await fetch(`${API}/research-workspaces/${activeWorkspace.id}`, { method: "DELETE" }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Unable to delete workspace.");
      setActiveWorkspace(null); setActiveReport(null); setWorkspaceReports([]); setWorkspaceMessage("Workspace deleted."); await loadWorkspaces();
    } catch (error) { setWorkspaceError(error.message); }
  };

  const uploadPaper = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.type !== "application/pdf") {
      setUploadError("Please upload a PDF file.");
      return;
    }
    setUploading(true);
    setUploadError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch(`${API}/papers/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to upload paper.");
      await loadPapers();
      setSelectedPaper(data.paper_id);
      setClaimMessage(`Uploaded and indexed ${data.filename}. You can now extract its claims.`);
      setActiveView("claims");
    } catch (error) {
      setUploadError(error.message || "Something went wrong.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };
  const askQuestion = async () => {
    if (!question.trim()) return;
    setAsking(true);
    setAskError("");
    setAnswer("");
    setSources([]);
    try {
      const response = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: 5 }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to generate answer.");
      setAnswer(data.answer || "");
      setSources(data.sources || []);
    } catch (error) {
      setAskError(error.message || "Something went wrong.");
    } finally {
      setAsking(false);
    }
  };
  const extractClaims = async () => {
    if (!selectedPaper) {
      setClaimError("Select a paper from the knowledge base first.");
      return;
    }
    setClaimLoading(true);
    setClaimError("");
    setClaimMessage("");
    try {
      const response = await fetch(
        `${API}/papers/${encodeURIComponent(selectedPaper)}/claims/extract`,
        { method: "POST" }
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Claim extraction failed.");
      setClaimMessage(
        `Processed ${data.chunks_processed} chunks and stored ${data.claims_created} source-verified claims.`
      );
      await loadClaimsAndGraph();
      await loadPapers();
    } catch (error) {
      setClaimError(error.message);
    } finally {
      setClaimLoading(false);
    }
  };

  const analyzeRelationships = async () => {
    setRelationshipLoading(true);
    setClaimError("");
    setClaimMessage("");
    try {
      const response = await fetch(`${API}/claims/relationships/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ similarity_threshold: 0.62, max_pairs: 100 }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Relationship analysis failed.");
      setClaimMessage(
        `Analyzed ${data.candidate_pairs} cross-paper candidate pairs and saved ${data.relationships_created} relationships.`
      );
      await loadClaimsAndGraph();
    } catch (error) {
      setClaimError(error.message);
    } finally {
      setRelationshipLoading(false);
    }
  };
  const refreshGraph = async () => {
    setClaimError("");
    try {
      await loadClaimsAndGraph();
      setClaimMessage("Claim graph refreshed.");
    } catch (error) {
      setClaimError(error.message);
    }
  };

  const loadReviews = async () => {
    setReviewsLoading(true);
    try {
      const response = await fetch(`${API}/future-reviewer/reviews`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to load previous reviews.");
      setReviews(data.reviews || []);
    } finally {
      setReviewsLoading(false);
    }
  };

  const updateReviewField = (event) => {
    const { name, value } = event.target;
    setReviewForm((current) => ({ ...current, [name]: value }));
  };

  const submitResearchProposal = async (event) => {
    event.preventDefault();
    setReviewLoading(true);
    setReviewError("");
    setReviewMessage("");
    setSelectedReview(null);
    try {
      const response = await fetch(`${API}/future-reviewer/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reviewForm),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Future Reviewer analysis failed.");
      setSelectedReview(data);
      setReviewMessage("Your research proposal has been reviewed successfully.");
      await loadReviews();
    } catch (error) {
      setReviewError(error.message || "Something went wrong while generating the review.");
    } finally {
      setReviewLoading(false);
    }
  };

  const openPreviousReview = async (reviewId) => {
    setReviewError("");
    try {
      const response = await fetch(`${API}/future-reviewer/reviews/${encodeURIComponent(reviewId)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to open this review.");
      setSelectedReview(data);
    } catch (error) {
      setReviewError(error.message);
    }
  };
  // Phase 4: Research Debate API actions
  const loadDebates = async () => {
    setDebatesLoading(true);
    try {
      const response = await fetch(`${API}/research-debate`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to load saved debates.");
      }
      setDebates(data.debates || []);
    } finally {
      setDebatesLoading(false);
    }
  };

  const runResearchDebate = async () => {
    if (!debateReviewId) {
      setDebateError("Select a Future Reviewer report first.");
      return;
    }

    setDebateLoading(true);
    setDebateError("");
    setDebateMessage("");
    setSelectedDebate(null);

    try {
      const response = await fetch(`${API}/research-debate/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ future_review_id: debateReviewId }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Research Debate failed.");
      }
      setSelectedDebate(data);
      setDebateMessage("Research Debate completed successfully.");
      await loadDebates();
    } catch (error) {
      setDebateError(error.message || "Unable to run the debate.");
    } finally {
      setDebateLoading(false);
    }
  };

  const openPreviousDebate = async (debateId) => {
    setDebateError("");
    try {
      const response = await fetch(
        `${API}/research-debate/${encodeURIComponent(debateId)}`
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to open this debate.");
      }
      setSelectedDebate(data);
      setDebateReviewId(data.future_review_id || "");
    } catch (error) {
      setDebateError(error.message || "Unable to open this debate.");
    }
  };

  // Phase 5: Research Reality Simulator API actions
  const loadRealityAssessments = async () => {
    setRealityHistoryLoading(true);

    try {
      const response = await fetch(`${API}/reality-simulator`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to load reality assessments.");
      }

      setRealityAssessments(data.assessments || []);
    } finally {
      setRealityHistoryLoading(false);
    }
  };


  const runRealitySimulation = async () => {
    if (!realityReviewId) {
      setRealityError("Select a Future Reviewer report first.");
      return;
    }

    setRealityLoading(true);
    setRealityError("");
    setRealityMessage("");
    setSelectedAssessment(null);

    try {
      const response = await fetch(`${API}/reality-simulator/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          future_review_id: realityReviewId,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Reality simulation failed.");
      }

      setSelectedAssessment(data);
      setRealityMessage("Reality simulation completed successfully.");

      await loadRealityAssessments();

    } catch (error) {
      setRealityError(error.message || "Unable to run reality simulation.");
    } finally {
      setRealityLoading(false);
    }
  };


  const openPreviousAssessment = async (assessmentId) => {
    setRealityError("");

    try {
      const response = await fetch(
        `${API}/reality-simulator/${encodeURIComponent(assessmentId)}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to open this assessment.");
      }

      setSelectedAssessment(data);
      setRealityReviewId(data.future_review_id || "");

    } catch (error) {
      setRealityError(error.message || "Unable to open assessment.");
    }
  };

  const relationshipLabel = (type) => (type || "").replaceAll("_", " ");

  const loadInsights = async (type = "") => {
    const query = type
      ? `?insight_type=${encodeURIComponent(type)}`
      : "";

    const response = await fetch(`${API}/insights${query}`);

    if (!response.ok) {
      throw new Error("Unable to load research insights.");
    }

    const data = await response.json();
    setInsights(data.insights || []);
  };

  const analyzeInsights = async (type) => {
    setInsightLoading(true);
    setInsightError("");
    setInsightMessage("");
    setInsightType(type);

    const endpoint =
      type === "blind_spot"
        ? "/insights/blind-spots/analyze"
        : "/insights/serendipity/analyze";

    try {
      const response = await fetch(`${API}${endpoint}`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed.");
      }

      setInsightMessage(
        `Successfully generated ${data.insights_generated} research insights.`
      );

      await loadInsights(type);
    } catch (error) {
      setInsightError(error.message);
    } finally {
      setInsightLoading(false);
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><BookOpen size={22} /></div>
          <div>
            <h1>ResearchX</h1>
            <span>Research Intelligence</span>
          </div>
        </div>
        <div className="sidebar-section">
          <div className="section-title">
            <span>KNOWLEDGE BASE</span>
            <span className="paper-count">{papers.length}</span>
          </div>
          <label className="upload-box">
            {uploading ? <LoaderCircle size={22} className="spin" /> : <Upload size={22} />}
            <strong>{uploading ? "Processing paper..." : "Upload research paper"}</strong>
            <p>PDF files up to 20MB</p>
            <span className="upload-button">
              <Upload size={16} /> {uploading ? "Uploading..." : "Choose PDF"}
            </span>
            <input type="file" accept=".pdf,application/pdf" onChange={uploadPaper} hidden disabled={uploading} />
          </label>
          {uploadError && <div className="upload-error">{uploadError}</div>}
        </div>

        <div className="papers-list">
          {papers.map((item) => (
            <button
              type="button"
              key={item.paper_id}
              className={`paper-item ${selectedPaper === item.paper_id ? "paper-item-active" : ""}`}
              onClick={() => setSelectedPaper(item.paper_id)}
            >
              <FileText size={18} />
              <span className="paper-item-copy">
                <strong>{item.filename || item.paper_id}</strong>
                <small>{item.pages} pages · {item.chunks} chunks · {item.claims_count || 0} claims</small>
              </span>
            </button>
          ))}
          {papers.length === 0 && <div className="papers-empty"><FileText size={20} /><p>Your research papers will appear here.</p></div>}
        </div>
        <div className="sidebar-bottom"><span>ResearchX</span><span>v1.1 · Claim Graph</span></div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">RESEARCH WORKSPACE</span>
            <h2>Understand your research.</h2>
          </div>
          <div className="status"><span className="status-dot" /> System ready</div>
        </header>

        <section className="workspace">
          <div className="view-tabs">
            <button className={activeView === "ask" ? "view-tab active" : "view-tab"} onClick={() => setActiveView("ask")}>
              <Sparkles size={16} /> Ask ResearchX
            </button>
            <button className={activeView === "claims" ? "view-tab active" : "view-tab"} onClick={() => setActiveView("claims")}>
              <Network size={16} /> Verifiable Claim Graph
            </button>
            <button
              className={
                activeView === "intelligence"
                  ? "view-tab active"
                  : "view-tab"
              }
              onClick={() => setActiveView("intelligence")}
            >
              <Lightbulb size={16} />
              Research Intelligence
            </button>
            <button
              className={activeView === "reviewer" ? "view-tab active" : "view-tab"}
              onClick={() => setActiveView("reviewer")}
            >
              <FileCheck2 size={16} /> Future Reviewer
            </button>
            <button
              className={activeView === "debate" ? "view-tab active" : "view-tab"}
              onClick={() => setActiveView("debate")}
            >
              <Scale size={16} /> Research Debate
            </button>
            <button
              className={activeView === "reality" ? "view-tab active" : "view-tab"}
              onClick={() => setActiveView("reality")}
            >
              <Gauge size={16} />
              Reality Simulator
            </button>
            <button
              className={activeView === "workflow" ? "view-tab active" : "view-tab"}
              onClick={() => setActiveView("workflow")}
            >
              <Bot size={16} />
              Agentic Workflow
            </button>
            <button className={activeView === "workspace" ? "view-tab active" : "view-tab"} onClick={() => setActiveView("workspace")}>
              <FolderKanban size={16} /> Research Workspace
            </button>
          </div>
          {activeView === "ask" ? (
            <>
              <div className="welcome">
                <div className="welcome-icon"><Sparkles size={28} /></div>
                <div>
                  <h3>Ask ResearchX</h3>
                  <p>Upload research papers and ask questions grounded in their content.</p>
                </div>
              </div>

              <div className="question-card">
                <label>RESEARCH QUESTION</label>
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="Ask something about your research papers..."
                  rows={4}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && event.ctrlKey) askQuestion();
                  }}
                />
                <div className="question-footer">
                  <span>Ctrl + Enter to ask</span>
                  <button className="ask-button" onClick={askQuestion} disabled={!question.trim() || asking}>
                    {asking ? <LoaderCircle size={17} className="spin" /> : <Search size={17} />}
                    {asking ? "Researching..." : "Ask ResearchX"}
                  </button>
                </div>
              </div>

              {askError && <div className="ask-error">{askError}</div>}

              <div className="answer-card">
                <div className="card-header">
                  <div><span className="card-label">RESEARCHX ANSWER</span><h3>Answer</h3></div>
                  {answer && <span className="grounded-badge">Evidence grounded</span>}
                </div>
                {asking ? (
                  <div className="answer-placeholder"><LoaderCircle size={24} className="spin" /><p>Researching your question...</p><span>Retrieving relevant evidence from your papers.</span></div>
                ) : answer ? (
                  <div className="answer-content">{answer}</div>
                ) : (
                  <div className="answer-placeholder"><Sparkles size={22} /><p>Your research answer will appear here.</p><span>Ask a question to retrieve evidence from your papers.</span></div>
                )}
              </div>
              <div className="sources-card">
                <div className="card-header">
                  <div><span className="card-label">EVIDENCE</span><h3>Sources</h3></div>
                  <ChevronDown size={20} />
                </div>
                {sources.length > 0 ? (
                  <div className="sources-list">
                    {sources.map((source, index) => (
                      <div className="source-item" key={`${source.paper_id}-${source.page_number}-${index}`}>
                        <div className="source-number">{index + 1}</div>
                        <div className="source-info">
                          <div className="source-title"><strong>{source.paper_id || "Research Paper"}</strong><span>Page {source.page_number}</span></div>
                          <p>{source.text}</p>
                        </div>
                        <ExternalLink size={16} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="sources-empty"><FileText size={20} /><span>Retrieved paper sections will appear here.</span></div>
                )}
              </div>
            </>
          ) : activeView === "claims" ? (
            <>
              <div className="claims-heading">
                <div className="welcome-icon"><GitBranch size={26} /></div>
                <div>
                  <h3>Verifiable Claim Graph</h3>
                  <p>Extract checkable claims, preserve exact source evidence, and compare findings across papers.</p>
                </div>
              </div>
              <div className="claim-toolbar">
                <div>
                  <strong>{selectedPaper ? "Selected paper" : "All indexed papers"}</strong>
                  <small>{selectedPaper || "Relationships are analyzed across all papers."}</small>
                </div>
                <button className="secondary-button" onClick={refreshGraph}><RefreshCw size={15} /> Refresh</button>
                <button className="ask-button" onClick={extractClaims} disabled={!selectedPaper || claimLoading}>
                  {claimLoading ? <LoaderCircle size={16} className="spin" /> : <FileSearch size={16} />}
                  {claimLoading ? "Extracting..." : "Extract claims"}
                </button>
              </div>

              {claimMessage && <div className="claim-success"><CheckCircle2 size={17} />{claimMessage}</div>}
              {claimError && <div className="ask-error"><AlertCircle size={16} />{claimError}</div>}

              <div className="claim-stats">
                <div><strong>{graph.nodes?.length || claims.length}</strong><span>Claims in view</span></div>
                <div><strong>{graph.edges?.length || 0}</strong><span>Relationships</span></div>
                <div><strong>{papers.length}</strong><span>Indexed papers</span></div>
              </div>

              <div className="claim-section-header">
                <div><span className="card-label">SOURCE-VERIFIED STATEMENTS</span><h3>Extracted claims</h3></div>
              </div>

              {claims.length ? (
                <div className="claim-list">
                  {claims.map((claim) => (
                    <article className="claim-card" key={claim.id}>
                      <div className="claim-card-top">
                        <span className="claim-type">{claim.claim_type}</span>
                        <span className="claim-paper">{claim.paper_id}</span>
                      </div>
                      <h4>{claim.claim_text}</h4>
                      {claim.evidence?.map((evidence, index) => (
                        <div className="claim-evidence" key={`${claim.id}-${index}`}>
                          <strong>Verbatim evidence · Page {evidence.page_number}</strong>
                          <p>“{evidence.quote}”</p>
                          <small>Chunk {evidence.chunk_id}{evidence.char_start != null ? ` · Characters ${evidence.char_start}–${evidence.char_end}` : ""}</small>
                        </div>
                      ))}
                      <div className="claim-conditions">
                        <strong>Experimental conditions</strong>
                        <pre>{JSON.stringify(claim.conditions || {}, null, 2)}</pre>
                      </div>
                      {claim.limitations && <p className="claim-limitation"><strong>Reported limitation:</strong> {claim.limitations}</p>}
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-panel">
                  <FileSearch size={24} />
                  <strong>No claims extracted yet</strong>
                  <span>Select a paper and click “Extract claims”. Extraction calls the configured LLM and verifies every evidence quotation against its original text chunk.</span>
                </div>
              )}
              <div className="claim-section-header relationship-header">
                <div><span className="card-label">CROSS-PAPER ANALYSIS</span><h3>Claim relationships</h3></div>
                <button className="ask-button" onClick={analyzeRelationships} disabled={relationshipLoading || claims.length < 2}>
                  {relationshipLoading ? <LoaderCircle size={16} className="spin" /> : <GitBranch size={16} />}
                  {relationshipLoading ? "Comparing..." : "Analyze relationships"}
                </button>
              </div>
              {graph.edges?.length ? (
                <div className="relationship-list">
                  {graph.edges.map((edge) => {
                    const source = graph.nodes.find((node) => node.id === edge.source);
                    const target = graph.nodes.find((node) => node.id === edge.target);
                    return (
                      <article className="relationship-card" key={edge.id}>
                        <div className="relationship-type">{relationshipLabel(edge.relationship_type)}</div>
                        <div className="relationship-claims">
                          <p><strong>Claim A:</strong> {source?.label || edge.source}</p>
                          <p><strong>Claim B:</strong> {target?.label || edge.target}</p>
                        </div>
                        <p>{edge.explanation}</p>
                        <small>Semantic similarity: {Number(edge.similarity || 0).toFixed(3)}</small>
                        <details>
                          <summary>Condition comparison</summary>
                          <pre>{JSON.stringify(edge.condition_differences || {}, null, 2)}</pre>
                        </details>
                      </article>
                    );
                  })}
                </div>
              ) : (
                <div className="empty-panel compact">
                  <Network size={22} />
                  <span>No cross-paper relationships yet. Extract claims from at least two papers, then analyze relationships.</span>
                </div>
              )}
              <p className="research-disclaimer">ResearchX labels are AI-assisted assessments, not proof of scientific truth. Verify conflict classifications against the original studies.</p>
            </>
          ) : activeView === "reviewer" ? (
            <section className="future-reviewer-section">
              <div className="claims-heading">
                <div className="welcome-icon"><FileCheck2 size={26} /></div>
                <div>
                  <h3>Future Reviewer</h3>
                  <p>Evaluate a proposed research direction against claims and evidence extracted from your uploaded papers.</p>
                </div>
              </div>

              <div className="reviewer-notice">
                <AlertCircle size={17} />
                <span>Novelty is assessed only against your uploaded ResearchX corpus. This is an AI-assisted review, not proof that an idea is globally novel or scientifically valid.</span>
              </div>
              {reviewError && <div className="ask-error"><AlertCircle size={16} />{reviewError}</div>}
              {reviewMessage && <div className="claim-success"><CheckCircle2 size={17} />{reviewMessage}</div>}

              <form className="review-form" onSubmit={submitResearchProposal}>
                <div className="review-form-heading">
                  <span className="card-label">NEW PROPOSAL</span>
                  <h3>Submit your research idea</h3>
                  <p>Provide as much detail as possible for a more useful review.</p>
                </div>
                <label htmlFor="research_title">Research title <span>*</span></label>
                <input id="research_title" name="research_title" value={reviewForm.research_title} onChange={updateReviewField} placeholder="e.g. A hybrid model for early disease detection" minLength={5} maxLength={500} required />

                <label htmlFor="research_idea">Research idea <span>*</span></label>
                <textarea id="research_idea" name="research_idea" value={reviewForm.research_idea} onChange={updateReviewField} placeholder="Describe the problem, research objective, proposed contribution, and what you want to investigate..." rows={5} minLength={20} maxLength={10000} required />

                <label htmlFor="proposed_methodology">Proposed methodology</label>
                <textarea id="proposed_methodology" name="proposed_methodology" value={reviewForm.proposed_methodology} onChange={updateReviewField} placeholder="Describe the model, approach, experiments, and workflow..." rows={4} maxLength={10000} />

                <div className="review-form-grid">
                  <div>
                    <label htmlFor="proposed_dataset">Proposed dataset</label>
                    <textarea id="proposed_dataset" name="proposed_dataset" value={reviewForm.proposed_dataset} onChange={updateReviewField} placeholder="Dataset names, sources, sample size..." rows={3} maxLength={3000} />
                  </div>
                  <div>
                    <label htmlFor="proposed_metrics">Evaluation metrics</label>
                    <textarea id="proposed_metrics" name="proposed_metrics" value={reviewForm.proposed_metrics} onChange={updateReviewField} placeholder="Accuracy, F1-score, AUC, ablation studies..." rows={3} maxLength={3000} />
                  </div>
                </div>
                <div className="review-form-footer">
                  <span>Required fields are marked with *</span>
                  <button className="ask-button" type="submit" disabled={reviewLoading || reviewForm.research_title.trim().length < 5 || reviewForm.research_idea.trim().length < 20}>
                    {reviewLoading ? <LoaderCircle size={16} className="spin" /> : <Sparkles size={16} />}
                    {reviewLoading ? "Reviewing proposal..." : "Generate AI review"}
                  </button>
                </div>
              </form>

              <div className="claim-section-header reviewer-history-heading">
                <div><span className="card-label">SAVED REPORTS</span><h3>Previous reviews</h3></div>
                <button className="secondary-button" type="button" onClick={() => loadReviews().catch((error) => setReviewError(error.message))} disabled={reviewsLoading}>
                  <RefreshCw size={15} className={reviewsLoading ? "spin" : ""} /> Refresh
                </button>
              </div>
              {reviews.length > 0 ? (
                <div className="review-history-list">
                  {reviews.map((review) => (
                    <button type="button" className={`review-history-item ${selectedReview?.id === review.id ? "selected" : ""}`} key={review.id} onClick={() => openPreviousReview(review.id)}>
                      <span><strong>{review.research_title}</strong><small>{review.created_at ? new Date(review.created_at).toLocaleString() : "Saved review"}</small></span>
                      <ExternalLink size={16} />
                    </button>
                  ))}
                </div>
              ) : (
                <div className="empty-panel compact"><ClipboardList size={22} /><span>No saved reviews yet. Submit a proposal to create your first report.</span></div>
              )}
              {selectedReview && (
                <div className="review-report">
                  <div className="review-report-header">
                    <div><span className="card-label">FUTURE REVIEW REPORT</span><h3>{selectedReview.research_title}</h3></div>
                    <span className="review-confidence">Confidence: {Math.round((Number(selectedReview.confidence) || 0) * 100)}%</span>
                  </div>
                  <section className="review-result-section">
                    <h4><Sparkles size={17} /> Novelty assessment</h4>
                    <p>{selectedReview.novelty_assessment?.assessment || "No assessment provided."}</p>
                    {selectedReview.novelty_assessment?.potential_novelty && <p><strong>Potential novelty:</strong> {selectedReview.novelty_assessment.potential_novelty}</p>}
                    {selectedReview.novelty_assessment?.differentiation && <p><strong>Differentiation:</strong> {selectedReview.novelty_assessment.differentiation}</p>}
                    {selectedReview.novelty_assessment?.existing_similar_work?.length > 0 && <div className="review-sublist"><strong>Similar work in your corpus</strong>{selectedReview.novelty_assessment.existing_similar_work.map((item, index) => <div key={index}><p>{item.description}</p>{item.claim_ids?.length > 0 && <small>Supporting claim IDs: {item.claim_ids.join(", ")}</small>}</div>)}</div>}
                  </section>
                  <section className="review-result-section">
                    <h4><ClipboardList size={17} /> Methodology review</h4>
                    {selectedReview.methodology_review?.feasibility && <p><strong>Feasibility:</strong> {selectedReview.methodology_review.feasibility}</p>}
                    {selectedReview.methodology_review?.evaluation_review && <p>{selectedReview.methodology_review.evaluation_review}</p>}
                    <ReviewBulletList title="Strengths" items={selectedReview.methodology_review?.strengths} />
                    <ReviewBulletList title="Concerns" items={selectedReview.methodology_review?.concerns} />
                  </section>
                  <section className="review-result-section">
                    <h4><MessageCircleQuestion size={17} /> Reviewer questions</h4>
                    {selectedReview.reviewer_questions?.length ? selectedReview.reviewer_questions.map((item, index) => <div className="review-point" key={index}><strong>{item.question}</strong><p>{item.reason}</p><small>Severity: {item.severity || "medium"}</small></div>) : <p>No reviewer questions returned.</p>}
                  </section>
                  <section className="review-result-section">
                    <h4><AlertCircle size={17} /> Potential weaknesses</h4>
                    {selectedReview.weaknesses?.length ? selectedReview.weaknesses.map((item, index) => <div className="review-point" key={index}><strong>{item.issue}</strong><p>{item.explanation}</p><small>Impact: {item.impact || "medium"}</small>{item.claim_ids?.length > 0 && <small> · Claims: {item.claim_ids.join(", ")}</small>}</div>) : <p>No weaknesses returned.</p>}
                  </section>
                  <section className="review-result-section">
                    <h4><Lightbulb size={17} /> Improvement suggestions</h4>
                    {selectedReview.improvement_suggestions?.length ? selectedReview.improvement_suggestions.map((item, index) => <div className="review-point" key={index}><strong>{item.suggestion}</strong><p>{item.expected_benefit}</p><small>Priority: {item.priority || "medium"}</small></div>) : <p>No suggestions returned.</p>}
                  </section>
                  {selectedReview.supporting_claim_ids?.length > 0 && <details className="review-supporting-claims"><summary>Supporting claim IDs</summary><ul>{selectedReview.supporting_claim_ids.map((id) => <li key={id}><code>{id}</code></li>)}</ul></details>}
                  <p className="research-disclaimer">This report compares the proposal with claims available in your uploaded papers only. Review the cited papers and evidence yourself before making research decisions.</p>
                </div>
              )}
            </section>
          ) : activeView === "debate" ? (
            <section className="research-debate-section">
              <div className="claims-heading">
                <div className="welcome-icon"><Scale size={26} /></div>
                <div>
                  <h3>Research Debate</h3>
                  <p>Challenge your research proposal through opposing AI teams and receive an independent verdict.</p>
                </div>
              </div>

              <div className="reviewer-notice">
                <AlertCircle size={17} />
                <span>This debate uses a saved Future Reviewer report and evidence from your uploaded research corpus. Conclusions are limited by the available evidence.</span>
              </div>

              {debateError && <div className="ask-error"><AlertCircle size={16} />{debateError}</div>}
              {debateMessage && <div className="claim-success"><CheckCircle2 size={17} />{debateMessage}</div>}

              <div className="debate-launch-card">
                <span className="card-label">START A NEW DEBATE</span>
                <h3>Select a research proposal</h3>
                <p>Choose an existing Future Reviewer report. You do not need to enter your proposal again.</p>
                <select
                  value={debateReviewId}
                  onChange={(event) => {
                    setDebateReviewId(event.target.value);
                    setSelectedDebate(null);
                    setDebateError("");
                    setDebateMessage("");
                  }}
                  disabled={debateLoading}
                >
                  <option value="">Choose a saved review...</option>
                  {reviews.map((review) => (
                    <option key={review.id} value={review.id}>
                      {review.research_title || review.id}
                    </option>
                  ))}
                </select>
                <button className="ask-button" onClick={runResearchDebate} disabled={!debateReviewId || debateLoading}>
                  {debateLoading ? <LoaderCircle size={16} className="spin" /> : <Swords size={16} />}
                  {debateLoading ? "Running three-stage debate..." : "Start Research Debate"}
                </button>
                {debateLoading && <p className="debate-loading-note">Blue Team is preparing its defence, Red Team is challenging the proposal, and the Judge is evaluating both sides. This may take a little time.</p>}
                {!reviews.length && !reviewsLoading && <p className="debate-loading-note">No saved reviews found. Generate a Future Reviewer report first.</p>}
              </div>

              {selectedDebate && (
                <div className="debate-results">
                  <div className="debate-result-header">
                    <div><span className="card-label">COMPLETED RESEARCH DEBATE</span><h3>Debate results</h3></div>
                    <span className="review-confidence">Confidence: {Math.round((Number(selectedDebate.confidence) || 0) * 100)}%</span>
                  </div>

                  <div className="debate-team-grid">
                    <article className="debate-team-card blue-team">
                      <div className="debate-team-heading"><ShieldCheck size={23} /><div><span>BLUE TEAM</span><h3>Defence</h3></div></div>
                      <p className="debate-position">{selectedDebate.blue_team?.position || "No position provided."}</p>
                      {selectedDebate.blue_team?.arguments?.length ? selectedDebate.blue_team.arguments.map((argument, index) => (
                        <div className="debate-argument" key={index}>
                          <strong>{argument.title || `Argument ${index + 1}`}</strong>
                          <p>{argument.argument || argument.rationale || "No argument details provided."}</p>
                          {argument.rationale && argument.argument && <p>{argument.rationale}</p>}
                          {argument.claim_ids?.length > 0 && <small>Claims: {argument.claim_ids.join(", ")}</small>}
                          {argument.strength && <small>Strength: {argument.strength}</small>}
                        </div>
                      )) : <p>No defence arguments were returned.</p>}
                      <div className="debate-assessment"><strong>Overall assessment</strong><p>{selectedDebate.blue_team?.overall_assessment || "No assessment provided."}</p></div>
                    </article>

                    <article className="debate-team-card red-team">
                      <div className="debate-team-heading"><Swords size={23} /><div><span>RED TEAM</span><h3>Challenge</h3></div></div>
                      <p className="debate-position">{selectedDebate.red_team?.position || "No position provided."}</p>
                      {selectedDebate.red_team?.arguments?.length ? selectedDebate.red_team.arguments.map((argument, index) => (
                        <div className="debate-argument" key={index}>
                          <strong>{argument.title || `Challenge ${index + 1}`}</strong>
                          <p>{argument.challenge || argument.reasoning || "No challenge details provided."}</p>
                          {argument.reasoning && argument.challenge && <p>{argument.reasoning}</p>}
                          {argument.claim_ids?.length > 0 && <small>Claims: {argument.claim_ids.join(", ")}</small>}
                          {argument.severity && <small>Severity: {argument.severity}</small>}
                        </div>
                      )) : <p>No challenge arguments were returned.</p>}
                      <div className="debate-assessment"><strong>Overall assessment</strong><p>{selectedDebate.red_team?.overall_assessment || "No assessment provided."}</p></div>
                    </article>
                  </div>

                  <article className="judge-verdict-card">
                    <div className="judge-heading"><Scale size={25} /><div><span className="card-label">INDEPENDENT EVALUATION</span><h3>Judge's final verdict</h3></div></div>
                    {selectedDebate.judge_verdict?.decision && <div className="judge-decision"><span>Decision</span><strong>{String(selectedDebate.judge_verdict.decision).replaceAll("_", " ")}</strong></div>}
                    <h4>{selectedDebate.judge_verdict?.verdict || "Verdict"}</h4>
                    <p>{selectedDebate.judge_verdict?.reasoning || "No reasoning provided."}</p>
                    {selectedDebate.judge_verdict?.blue_team_assessment && <div className="debate-assessment"><strong>Blue Team evaluation</strong><p>{selectedDebate.judge_verdict.blue_team_assessment}</p></div>}
                    {selectedDebate.judge_verdict?.red_team_assessment && <div className="debate-assessment"><strong>Red Team evaluation</strong><p>{selectedDebate.judge_verdict.red_team_assessment}</p></div>}
                    <ReviewBulletList title="Strongest arguments" items={selectedDebate.judge_verdict?.winning_arguments} />
                    <ReviewBulletList title="Unresolved risks" items={selectedDebate.judge_verdict?.unresolved_risks} />
                    <ReviewBulletList title="Recommendations" items={selectedDebate.judge_verdict?.recommendations} />
                    {selectedDebate.judge_verdict?.evidence_assessment && <div className="debate-assessment"><strong>Evidence assessment</strong><p>{selectedDebate.judge_verdict.evidence_assessment}</p></div>}
                    <details className="review-supporting-claims">
                      <summary>Validated supporting claim IDs</summary>
                      {selectedDebate.supporting_claim_ids?.length ? <ul>{selectedDebate.supporting_claim_ids.map((id) => <li key={id}><code>{id}</code></li>)}</ul> : <p>No supporting claim IDs were returned.</p>}
                    </details>
                  </article>
                  <p className="research-disclaimer">The verdict is an AI-assisted evaluation, not a scientific peer-review decision. Verify evidence against the original research papers.</p>
                </div>
              )}

              <div className="claim-section-header reviewer-history-heading">
                <div><span className="card-label">DEBATE HISTORY</span><h3>Previous debates</h3></div>
                <button className="secondary-button" onClick={() => loadDebates().catch((error) => setDebateError(error.message))} disabled={debatesLoading}>
                  <RefreshCw size={15} className={debatesLoading ? "spin" : ""} /> Refresh
                </button>
              </div>
              {debates.length ? (
                <div className="review-history-list">
                  {debates.map((debate) => (
                    <button type="button" className={`review-history-item ${selectedDebate?.id === debate.id ? "selected" : ""}`} key={debate.id} onClick={() => openPreviousDebate(debate.id)}>
                      <span><strong>{reviews.find((review) => review.id === debate.future_review_id)?.research_title || "Research Debate"}</strong><small>{debate.created_at ? new Date(debate.created_at).toLocaleString() : "Saved debate"}</small></span>
                      <ExternalLink size={16} />
                    </button>
                  ))}
                </div>
              ) : (
                <div className="empty-panel compact"><Swords size={22} /><span>{debatesLoading ? "Loading saved debates..." : "No saved debates yet. Select a research review above to start your first debate."}</span></div>
              )}
            </section>
          )  : activeView === "reality" ? (
            <section className="reality-simulator-section">
              <div className="reality-header">
                <div>
                  <h2>Research Reality Simulator</h2>
                  <p>
                    Evaluate whether your research proposal can realistically
                    be implemented with available resources, infrastructure,
                    budget and technical capabilities.
                  </p>
                </div>
                <Gauge size={32} />
              </div>

              <div className="reality-notice">
                <ShieldCheck size={18} />
                <p>
                  AI-generated feasibility estimates are indicative.
                  Verify infrastructure requirements, costs and ethical
                  considerations before implementation.
                </p>
              </div>

              {realityError && (
                <div className="error-message">
                  {realityError}
                </div>
              )}

              {realityMessage && (
                <div className="success-message">
                  {realityMessage}
                </div>
              )}

              <div className="reality-launcher">
                <h3>Evaluate a Research Proposal</h3>

                <label>Select a Future Reviewer Report</label>

                <select
                  value={realityReviewId}
                  onChange={(e) => setRealityReviewId(e.target.value)}
                >
                  <option value="">Choose a research proposal</option>

                  {reviews.map((review) => (
                    <option key={review.id} value={review.id}>
                      {review.title || `Review ${review.id}`}
                    </option>
                  ))}
                </select>

                <button
                  onClick={runRealitySimulation}
                  disabled={realityLoading || !realityReviewId}
                >
                  {realityLoading ? (
                    <>
                      <LoaderCircle className="spin" size={16} />
                      Simulating...
                    </>
                  ) : (
                    <>
                      <Gauge size={16} />
                      Run Reality Simulation
                    </>
                  )}
                </button>
              </div>

              {selectedAssessment && (
                <div className="reality-results">
                  <h2>Simulation Results</h2>

                  <div className="reality-score-grid">
                    <div className="reality-score-card">
                      <span>Feasibility Score</span>
                      <strong>
                        {Math.round(
                          Number(selectedAssessment.feasibility_score || 0) * 100
                        )}%
                      </strong>
                    </div>

                    <div className="reality-score-card">
                      <span>Confidence</span>
                      <strong>
                        {Math.round(
                          Number(selectedAssessment.confidence || 0) * 100
                        )}%
                      </strong>
                    </div>
                  </div>

                  <section className="reality-result-section">
                    <h3>Overall Assessment</h3>
                    <p>{selectedAssessment.overall_assessment}</p>
                  </section>

                  <RealityDetail
                    title="Technical Feasibility"
                    data={selectedAssessment.technical_feasibility}
                  />

                  <RealityDetail
                    title="Resource Requirements"
                    data={selectedAssessment.resource_requirements}
                  />

                  <RealityDetail
                    title="Cost Estimate"
                    data={selectedAssessment.cost_estimate}
                  />

                  <RealityDetail
                    title="Privacy and Ethics"
                    data={selectedAssessment.privacy_ethics}
                  />

                  <RealityDetail
                    title="Accessibility"
                    data={selectedAssessment.accessibility}
                  />

                  <section className="reality-result-section">
                    <h3>Identified Risks</h3>

                    {Array.isArray(selectedAssessment.risks) &&
                    selectedAssessment.risks.length > 0 ? (
                      selectedAssessment.risks.map((risk, index) => (
                        <div className="reality-list-item" key={index}>
                          <strong>{risk.risk || `Risk ${index + 1}`}</strong>
                          <p>Severity: {risk.severity || "Not specified"}</p>
                          <p>Likelihood: {risk.likelihood || "Not specified"}</p>
                          <p>Impact: {risk.impact || "Not specified"}</p>
                        </div>
                      ))
                    ) : (
                      <p>No risks listed.</p>
                    )}
                  </section>

                  <section className="reality-result-section">
                    <h3>Mitigation Strategies</h3>

                    {Array.isArray(selectedAssessment.mitigation_strategies) &&
                    selectedAssessment.mitigation_strategies.length > 0 ? (
                      selectedAssessment.mitigation_strategies.map((item, index) => (
                        <div className="reality-list-item" key={index}>
                          <strong>{item.risk || `Mitigation ${index + 1}`}</strong>
                          <p>{item.strategy || "No strategy specified"}</p>
                          <p>Priority: {item.priority || "Not specified"}</p>
                        </div>
                      ))
                    ) : (
                      <p>No mitigation strategies listed.</p>
                    )}
                  </section>
                </div>
              )}

              <div className="reality-history">
                <h3>Previous Simulations</h3>

                {realityHistoryLoading ? (
                  <p>Loading simulation history...</p>
                ) : realityAssessments.length === 0 ? (
                  <p>No previous simulations available.</p>
                ) : (
                  realityAssessments.map((assessment) => (
                    <button
                      className="reality-history-item"
                      key={assessment.id}
                      onClick={() => openPreviousAssessment(assessment.id)}
                    >
                      <div>
                        <strong>
                          {reviews.find(
                            (review) => review.id === assessment.future_review_id
                          )?.title || `Assessment ${assessment.id}`}
                        </strong>

                        <p>
                          {assessment.created_at
                            ? new Date(assessment.created_at).toLocaleString()
                            : "Date unavailable"}
                        </p>
                      </div>

                      <ExternalLink size={16} />
                    </button>
                  ))
                )}
              </div>
            </section>
          ) : activeView === "workflow" ? (
            <section className="agentic-workflow-section">
              <div className="claims-heading">
                <div className="welcome-icon"><Bot size={26} /></div>
                <div>
                  <h3>Agentic Research Workflow</h3>
                  <p>Describe a research task. ResearchX will plan a sequence of tools, execute the selected existing modules, and preserve the results.</p>
                </div>
              </div>

              <div className="workflow-notice">
                <ShieldCheck size={18} />
                <span>The agent can call only the ResearchX tools registered in its allowlist. Findings are limited to your uploaded papers and available evidence.</span>
              </div>

              {workflowError && <div className="ask-error"><AlertCircle size={16} />{workflowError}</div>}
              {workflowMessage && <div className="claim-success"><CheckCircle2 size={16} />{workflowMessage}</div>}

              <form className="workflow-launcher" onSubmit={runAgenticWorkflow}>
                <label htmlFor="workflow-request">WHAT WOULD YOU LIKE RESEARCHX TO DO?</label>
                <textarea
                  id="workflow-request"
                  rows={5}
                  value={workflowRequest}
                  onChange={(event) => setWorkflowRequest(event.target.value)}
                  placeholder="Example: Compare the main findings across my uploaded papers, identify conflicting claims, and suggest research gaps."
                />
                <label htmlFor="workflow-review">OPTIONAL: USE A SAVED FUTURE REVIEWER REPORT</label>
                <select id="workflow-review" value={workflowReviewId} onChange={(event) => setWorkflowReviewId(event.target.value)}>
                  <option value="">No saved proposal selected</option>
                  {reviews.map((review) => (
                    <option key={review.id} value={review.id}>{review.research_title || `Review ${review.id}`}</option>
                  ))}
                </select>
                <button className="ask-button" type="submit" disabled={workflowLoading || !workflowRequest.trim()}>
                  {workflowLoading ? <LoaderCircle size={16} className="spin" /> : <Play size={16} />}
                  {workflowLoading ? "Planning and executing..." : "Run ResearchX Workflow"}
                </button>
                <p className="workflow-help">Complex workflows may make several model calls. You can inspect the selected plan and individual tool outcomes after execution.</p>
              </form>

              {selectedWorkflow && (
                <div className="workflow-output">
                  <div className="workflow-output-heading">
                    <div><span className="card-label">EXECUTION RESULT</span><h3>Workflow report</h3></div>
                    <span className={`workflow-status ${selectedWorkflow.status}`}>{selectedWorkflow.status}</span>
                  </div>
                  <p className="workflow-summary">{selectedWorkflow.summary}</p>
                  <section className="workflow-plan">
                    <h4><Workflow size={17} /> Agent execution plan</h4>
                    {selectedWorkflow.plan?.map((step, index) => (
                      <div className="workflow-plan-step" key={`${step.tool}-${index}`}>
                        <span>{index + 1}</span><div><strong>{step.tool.replaceAll("_", " ")}</strong><p>{step.reason}</p></div>
                      </div>
                    ))}
                  </section>
                  <section className="workflow-tool-results">
                    <h4>Tool results</h4>
                    {selectedWorkflow.results?.map((item, index) => (
                      <details className="workflow-result-item" key={`${item.tool}-${index}`} open={index === 0}>
                        <summary><span>{item.tool.replaceAll("_", " ")}</span><span className={`workflow-status ${item.status}`}>{item.status}</span></summary>
                        {item.error && <p className="workflow-tool-error">{item.error}</p>}
                        {item.output && <pre>{JSON.stringify(item.output, null, 2)}</pre>}
                      </details>
                    ))}
                  </section>
                </div>
              )}

              <section className="workflow-history">
                <div className="section-heading"><h3><History size={18} /> Previous workflows</h3></div>
                {workflowHistoryLoading ? <p>Loading workflow history...</p> : workflowHistory.length === 0 ? <p>No workflows have been run yet.</p> : workflowHistory.map((item) => (
                  <button className="workflow-history-item" key={item.id} onClick={() => openPreviousWorkflow(item.id)}>
                    <div><strong>{item.user_request}</strong><p>{item.created_at ? new Date(item.created_at).toLocaleString() : "Date unavailable"}</p></div>
                    <span className={`workflow-status ${item.status}`}>{item.status}</span>
                  </button>
                ))}
              </section>
            </section>
          ) : activeView === "workspace" ? (
            <section className="phase7-section">
              <div className="claims-heading"><div className="welcome-icon"><FolderKanban size={26} /></div><div><h3>Research Workspace & Reports</h3><p>Organize selected papers, preserve research context, and generate evidence-linked reports from your ResearchX analyses.</p></div></div>
              <div className="workflow-notice"><ShieldCheck size={18} /><span>Paper claims and quotations are shown as source evidence. AI-generated insights, reviews and workflow summaries are labelled separately and should be verified against original papers.</span></div>
              {workspaceError && <div className="ask-error"><AlertCircle size={16} />{workspaceError}</div>}
              {workspaceMessage && <div className="claim-success"><CheckCircle2 size={16} />{workspaceMessage}</div>}
              <div className="phase7-grid">
                <section className="phase7-card"><h3><Plus size={18}/> Create a research workspace</h3>
                  <form className="workflow-launcher" onSubmit={createWorkspace}>
                    <label>WORKSPACE TITLE</label><input required minLength={3} value={workspaceForm.title} onChange={e=>setWorkspaceForm({...workspaceForm,title:e.target.value})} placeholder="e.g. Retinal Disease Detection Study"/>
                    <label>DESCRIPTION</label><textarea rows={2} value={workspaceForm.description} onChange={e=>setWorkspaceForm({...workspaceForm,description:e.target.value})} placeholder="Purpose, scope and context"/>
                    <label>RESEARCH QUESTION</label><textarea rows={3} value={workspaceForm.research_question} onChange={e=>setWorkspaceForm({...workspaceForm,research_question:e.target.value})} placeholder="What question will this project investigate?"/>
                    <label>SELECT PAPERS</label><div className="phase7-paper-list">{papers.map(p=>{const paperId=p.paper_id;return <label key={paperId} className="phase7-paper-choice"><input type="checkbox" checked={workspaceForm.paper_ids.includes(paperId)} onChange={e=>setWorkspaceForm(f=>({...f,paper_ids:e.target.checked?[...f.paper_ids,paperId]:f.paper_ids.filter(id=>id!==paperId)}))}/><span>{p.filename || paperId}</span></label>})}</div>
                    <button className="ask-button" type="submit" disabled={workspaceLoading || !workspaceForm.title.trim()}>{workspaceLoading?<LoaderCircle className="spin" size={16}/>:<Plus size={16}/>} Create workspace</button>
                  </form>
                </section>
                <section className="phase7-card"><h3>Saved workspaces</h3>{workspaces.length===0?<p className="workflow-help">No workspaces yet. Create one to get started.</p>:workspaces.map(w=><button className="workflow-history-item" key={w.id} onClick={()=>openWorkspace(w.id)}><div><strong>{w.title}</strong><p>{w.papers?.length||0} papers · {w.report_count||0} reports</p></div><ExternalLink size={16}/></button>)}</section>
              </div>
              {activeWorkspace && <section className="phase7-card phase7-active"><div className="workflow-output-heading"><div><span className="card-label">ACTIVE PROJECT</span><h3>{activeWorkspace.title}</h3></div><button className="phase7-delete" onClick={deleteWorkspace}><Trash2 size={15}/> Delete</button></div>
                <form className="workflow-launcher" onSubmit={saveWorkspace}><label>TITLE</label><input value={workspaceForm.title} onChange={e=>setWorkspaceForm({...workspaceForm,title:e.target.value})}/><label>DESCRIPTION</label><textarea rows={2} value={workspaceForm.description} onChange={e=>setWorkspaceForm({...workspaceForm,description:e.target.value})}/><label>RESEARCH QUESTION</label><textarea rows={2} value={workspaceForm.research_question} onChange={e=>setWorkspaceForm({...workspaceForm,research_question:e.target.value})}/><label>LINKED PAPERS</label><div className="phase7-paper-list">{papers.map(p=>{const paperId=p.paper_id;return <label className="phase7-paper-choice" key={paperId}><input type="checkbox" checked={workspaceForm.paper_ids.includes(paperId)} onChange={e=>setWorkspaceForm(f=>({...f,paper_ids:e.target.checked?[...f.paper_ids,paperId]:f.paper_ids.filter(id=>id!==paperId)}))}/><span>{p.filename||paperId}</span></label>})}</div><button className="ask-button" type="submit" disabled={workspaceLoading}>Save workspace changes</button></form>
                <button className="ask-button" onClick={generateWorkspaceReport} disabled={workspaceLoading}>{workspaceLoading?<LoaderCircle className="spin" size={16}/>:<FileText size={16}/>} Generate research report</button>
                <h3>Report history</h3>{workspaceReports.map(r=><button className="workflow-history-item" key={r.id} onClick={()=>openReport(r.id)}><div><strong>{r.title}</strong><p>{new Date(r.created_at).toLocaleString()}</p></div><FileText size={16}/></button>)}
              </section>}
              {activeReport && <section className="phase7-card phase7-report"><div className="workflow-output-heading"><div><span className="card-label">SAVED REPORT</span><h2>{activeReport.title}</h2></div><div className="phase7-export"><a href={`${API}/research-reports/${activeReport.id}/export/pdf`} target="_blank" rel="noreferrer"><Download size={15}/> PDF</a><a href={`${API}/research-reports/${activeReport.id}/export/docx`} target="_blank" rel="noreferrer"><Download size={15}/> DOCX</a><a href={`${API}/research-reports/${activeReport.id}/export/txt`} target="_blank" rel="noreferrer"><Download size={15}/> TXT</a></div></div>
                {activeReport.sections?.map((sec,i)=><article className="phase7-report-section" key={`${sec.heading}-${i}`}><h3>{sec.heading}</h3>{sec.content&&<p>{sec.content}</p>}{sec.items?.length>0&&sec.items.map((item,j)=><details key={j}><summary>{item.filename||item.title||item.claim||item.request||item.paper_id||`Record ${j+1}`}</summary><pre>{JSON.stringify(item,null,2)}</pre></details>)}</article>)}
                <p className="workflow-help">Sources included: {activeReport.source_manifest?.map(x=>x.filename).join(", ") || "No papers selected"}</p>
              </section>}
            </section>
          ) : activeView === "intelligence" ? (
            <section className="intelligence-section">

              <div className="claims-heading">
                <div className="welcome-icon">
                  <Lightbulb size={26} />
                </div>
                <div>
                  <h3>Research Intelligence</h3>
                  <p>
                    Discover hidden research opportunities and
                    unexpected connections across your papers.
                  </p>
                </div>
              </div>

              {insightError && (
                <div className="ask-error">
                  <AlertCircle size={16} />
                  {insightError}
                </div>
              )}

              {insightMessage && (
                <div className="claim-success">
                  <CheckCircle2 size={17} />
                  {insightMessage}
                </div>
              )}

              <div className="intelligence-grid">

                <article className="intelligence-card">
                  <div className="intelligence-icon">
                    <Compass size={25} />
                  </div>

                  <span className="card-label">
                    RESEARCH COVERAGE ANALYSIS
                  </span>
                  <h3>Research Blind Spot Detector</h3>

                  <p>
                    Identify missing perspectives, underexplored
                    areas, assumptions and unanswered questions
                    within your uploaded research collection.
                  </p>

                  <button
                    className="ask-button"
                    disabled={insightLoading || claims.length === 0}
                    onClick={() => analyzeInsights("blind_spot")}
                  >
                    {insightLoading && insightType === "blind_spot"
                      ? <LoaderCircle size={16} className="spin" />
                      : <Compass size={16} />}

                    Detect blind spots
                  </button>
                </article>

                <article className="intelligence-card">
                  <div className="intelligence-icon">
                    <WandSparkles size={25} />
                  </div>

                  <span className="card-label">
                    CROSS-DOMAIN DISCOVERY
                  </span>
                  <h3>Research Serendipity Engine</h3>

                  <p>
                    Discover unexpected connections between
                    different research papers and generate
                    potentially useful research directions.
                  </p>

                  <button
                    className="ask-button"
                    disabled={
                      insightLoading ||
                      new Set(claims.map((claim) => claim.paper_id)).size < 2
                    }
                    onClick={() => analyzeInsights("serendipity")}
                  >
                    {insightLoading && insightType === "serendipity"
                      ? <LoaderCircle size={16} className="spin" />
                      : <WandSparkles size={16} />}

                    Discover connections
                  </button>
                </article>

              </div>
              <div className="claim-section-header">
                <div>
                  <span className="card-label">
                    GENERATED RESEARCH INSIGHTS
                  </span>
                  <h3>Discovery results</h3>
                </div>

                <button
                  className="secondary-button"
                  onClick={() => loadInsights().catch(
                    (error) => setInsightError(error.message)
                  )}
                >
                  <RefreshCw size={15} />
                  Refresh
                </button>
              </div>

              <div className="insight-filters">
                <button
                  className={insightType === "blind_spot" ? "filter-active" : ""}
                  onClick={() => {
                    setInsightType("blind_spot");
                    loadInsights("blind_spot");
                  }}
                >
                  Blind Spots
                </button>

                <button
                  className={insightType === "serendipity" ? "filter-active" : ""}
                  onClick={() => {
                    setInsightType("serendipity");
                    loadInsights("serendipity");
                  }}
                >
                  Serendipity
                </button>
              </div>
              {insightLoading ? (
                <div className="empty-panel">
                  <LoaderCircle size={25} className="spin" />
                  <strong>Analyzing your research...</strong>
                  <span>
                    ResearchX is examining extracted claims and
                    their evidence.
                  </span>
                </div>
              ) : insights.length > 0 ? (
                <div className="insight-list">
                  {insights.map((insight) => (
                    <article className="insight-card" key={insight.id}>

                      <div className="insight-card-top">
                        <span className="claim-type">
                          {insight.insight_type.replaceAll("_", " ")}
                        </span>

                        <span className="insight-confidence">
                          Confidence:{" "}
                          {(insight.confidence * 100).toFixed(0)}%
                        </span>
                      </div>

                      <h3>{insight.title}</h3>

                      <p>{insight.description}</p>

                      <div className="insight-rationale">
                        <strong>Why this matters</strong>
                        <p>{insight.rationale}</p>
                      </div>
                      {insight.suggested_question && (
                        <div className="insight-question">
                          <strong>Suggested research question</strong>
                          <p>{insight.suggested_question}</p>
                        </div>
                      )}

                      <details>
                        <summary>
                          Supporting claim IDs
                        </summary>

                        <ul>
                          {insight.supporting_claim_ids.map((id) => (
                            <li key={id}>
                              <code>{id}</code>
                            </li>
                          ))}
                        </ul>
                      </details>

                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-panel">
                  <Lightbulb size={24} />
                  <strong>No research insights yet</strong>
                  <span>
                    Run one of the analyses above to discover
                    research opportunities.
                  </span>
                </div>
              )}

              <p className="research-disclaimer">
                These insights are AI-generated hypotheses based
                on your uploaded papers. They are not proof of
                universal research gaps or established discoveries.
                Verify them against the original evidence.
              </p>

            </section>
          ) : null}
        </section>
      </main>
    </div>
  );
}
export default App;