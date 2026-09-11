import { useEffect, useState } from "react";

import {
  BookOpen,
  FileText,
  Upload,
  Search,
  Sparkles,
  ChevronDown,
  ExternalLink,
  LoaderCircle,
} from "lucide-react";

import "./App.css";


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


  // =========================
// LOAD KNOWLEDGE BASE
// =========================

const loadPapers = async () => {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/papers"
    );

    if (!response.ok) {
      throw new Error("Failed to load papers.");
    }

    const data = await response.json();

    setPapers(data.papers || []);

  } catch (error) {
    console.error(
      "Failed to load knowledge base:",
      error
    );
  }
};


useEffect(() => {
  loadPapers();
}, []);
  // =========================
  // UPLOAD PAPER
  // =========================

  const uploadPaper = async (event) => {

    const file = event.target.files[0];

    if (!file) {
      return;
    }

    if (file.type !== "application/pdf") {

      setUploadError(
        "Please upload a PDF file."
      );

      return;
    }

    setUploading(true);
    setUploadError("");

    const formData = new FormData();

    formData.append("file", file);


    try {

      const response = await fetch(
        "http://127.0.0.1:8000/papers/upload",
        {
          method: "POST",
          body: formData,
        }
      );


      const data = await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Failed to upload paper."
        );

      }

      await loadPapers();

      setSelectedPaper(data.paper_id);

    } catch (error) {

      setUploadError(
        error.message ||
        "Something went wrong."
      );

    } finally {

      setUploading(false);

    }
  };


  // =========================
  // ASK QUESTION
  // =========================

  const askQuestion = async () => {

    if (!question.trim()) {
      return;
    }

    setAsking(true);
    setAskError("");

    setAnswer("");
    setSources([]);


    try {

      const response = await fetch(
        "http://127.0.0.1:8000/ask",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            question: question,
            top_k: 5,
          }),
        }
      );


      const data = await response.json();


      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Failed to generate answer."
        );

      }


      /*
        Our backend returns:

        {
          answer: "...",
          sources: [...]
        }
      */

      setAnswer(
        data.answer || ""
      );

      setSources(
        data.sources || []
      );


    } catch (error) {

      setAskError(
        error.message ||
        "Something went wrong."
      );

    } finally {

      setAsking(false);

    }
  };


  return (

    <div className="app">


      {/* ================= SIDEBAR ================= */}

      <aside className="sidebar">


        <div className="brand">

          <div className="brand-icon">
            <BookOpen size={22} />
          </div>

          <div>

            <h1>ResearchX</h1>

            <span>
              Research Intelligence
            </span>

          </div>

        </div>


        <div className="sidebar-section">


          <div className="section-title">

            <span>
              KNOWLEDGE BASE
            </span>

            <span className="paper-count">
              {papers.length}
            </span>

          </div>


          <label className="upload-box">

            {uploading ? (
              <LoaderCircle
                size={22}
                className="spin"
              />
            ) : (
              <Upload size={22} />
            )}


            <strong>

              {uploading
                ? "Processing paper..."
                : "Upload research paper"}

            </strong>


            <p>
              PDF files up to 20MB
            </p>


            <span className="upload-button">

              <Upload size={16} />

              {uploading
                ? "Uploading..."
                : "Choose PDF"}

            </span>


            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={uploadPaper}
              hidden
              disabled={uploading}
            />

          </label>


          {uploadError && (

            <div className="upload-error">
              {uploadError}
            </div>

          )}

        </div>

        {/* PAPERS */}

        {papers.length > 0 ? (

          <div className="papers-list">

            {papers.map((item) => (

              <div
                key={item.paper_id}
                className={`paper-item ${
                  selectedPaper === item.paper_id
                    ? "paper-item-active"
                    : ""
                }`}
                onClick={() =>
                  setSelectedPaper(item.paper_id)
                }
              >

                <FileText size={20} />

                <div>

                  <strong>
                    {item.paper_id}
                  </strong>

                  <span>
                    {item.pages} pages ·{" "}
                    {item.chunks} chunks
                  </span>

                </div>

              </div>

            ))}

          </div>

        ) : (

          <div className="papers-empty">

            <FileText size={20} />

            <p>
              Your research papers
              will appear here.
            </p>

          </div>

        )}


        <div className="sidebar-bottom">

          <span>
            ResearchX
          </span>

          <span>
            v0.1
          </span>

        </div>

      </aside>


      {/* ================= MAIN ================= */}

      <main className="main">


        <header className="topbar">

          <div>

            <span className="eyebrow">
              RESEARCH WORKSPACE
            </span>

            <h2>
              Understand your research.
            </h2>

          </div>


          <div className="status">

            <span className="status-dot"></span>

            System ready

          </div>

        </header>


        <section className="workspace">


          {/* ================= WELCOME ================= */}

          <div className="welcome">

            <div className="welcome-icon">
              <Sparkles size={28} />
            </div>

            <div>

              <h3>
                Ask ResearchX
              </h3>

              <p>
                Upload research papers and ask
                questions grounded in their content.
              </p>

            </div>

          </div>


          {/* ================= QUESTION ================= */}

          <div className="question-card">

            <label>
              RESEARCH QUESTION
            </label>


            <textarea

              value={question}

              onChange={(e) =>
                setQuestion(e.target.value)
              }

              placeholder={
                "Ask something about your research papers..."
              }

              rows={4}

              onKeyDown={(e) => {

                if (
                  e.key === "Enter" &&
                  e.ctrlKey
                ) {
                  askQuestion();
                }

              }}

            />


            <div className="question-footer">

              <span>
                Ctrl + Enter to ask
              </span>


              <button

                className="ask-button"

                onClick={askQuestion}

                disabled={
                  !question.trim() ||
                  asking
                }

              >

                {asking ? (
                  <LoaderCircle
                    size={17}
                    className="spin"
                  />
                ) : (
                  <Search size={17} />
                )}


                {asking
                  ? "Researching..."
                  : "Ask ResearchX"}

              </button>

            </div>

          </div>


          {/* ================= ASK ERROR ================= */}

          {askError && (

            <div className="ask-error">
              {askError}
            </div>

          )}


          {/* ================= ANSWER ================= */}

          <div className="answer-card">

            <div className="card-header">

              <div>

                <span className="card-label">
                  RESEARCHX ANSWER
                </span>

                <h3>
                  Answer
                </h3>

              </div>


              {answer && (

                <span className="grounded-badge">
                  Evidence grounded
                </span>

              )}

            </div>


            {asking ? (

              <div className="answer-placeholder">

                <LoaderCircle
                  size={24}
                  className="spin"
                />

                <p>
                  Researching your question...
                </p>

                <span>
                  Retrieving relevant evidence
                  from your papers.
                </span>

              </div>

            ) : answer ? (

              <div className="answer-content">

                {answer}

              </div>

            ) : (

              <div className="answer-placeholder">

                <Sparkles size={22} />

                <p>
                  Your research answer will appear here.
                </p>

                <span>
                  Ask a question to retrieve evidence
                  from your papers.
                </span>

              </div>

            )}

          </div>


          {/* ================= SOURCES ================= */}

          <div className="sources-card">

            <div className="card-header">

              <div>

                <span className="card-label">
                  EVIDENCE
                </span>

                <h3>
                  Sources
                </h3>

              </div>

              <ChevronDown size={20} />

            </div>


            {sources.length > 0 ? (

              <div className="sources-list">

                {sources.map(
                  (source, index) => (

                    <div
                      className="source-item"
                      key={index}
                    >

                      <div className="source-number">
                        {index + 1}
                      </div>


                      <div className="source-info">

                        <div className="source-title">

                          <strong>
                            {source.paper_id ||
                              "Research Paper"}
                          </strong>

                          <span>
                            Page{" "}
                            {source.page_number}
                          </span>

                        </div>


                        <p>
                          {source.text}
                        </p>

                      </div>


                      <ExternalLink
                        size={16}
                      />

                    </div>

                  )
                )}

              </div>

            ) : (

              <div className="sources-empty">

                <FileText size={20} />

                <span>
                  Retrieved paper sections
                  will appear here.
                </span>

              </div>

            )}

          </div>


        </section>

      </main>

    </div>

  );

}


export default App;