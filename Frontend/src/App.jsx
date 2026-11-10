
import React, { useState, useRef, useEffect } from 'react';
import Results from './components/Results';

const API_URL = 'https://research-mind-7cj4.onrender.com/api/research';

const steps = [
  {
    icon: '⌕',
    title: 'Search',
    description: 'Finds relevant sources',
  },
  {
    icon: '▤',
    title: 'Read',
    description: 'Extracts key information',
  },
  {
    icon: '✎',
    title: 'Write',
    description: 'Generates a research report',
  },
  {
    icon: '◇',
    title: 'Critique',
    description: 'Evaluates and improves',
  },
];

export default function App() {
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);

  const stepTimerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (stepTimerRef.current) {
        clearInterval(stepTimerRef.current);
      }
    };
  }, []);

  const handleSubmit = async (e) => {
    e?.preventDefault();

    const trimmedTopic = topic.trim();

    if (!trimmedTopic) {
      setError('Please enter a research topic first.');
      return;
    }

    setError(null);
    setResults(null);
    setLoading(true);
    setCurrentStep(1);

    let stepCounter = 1;

    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current);
    }

    stepTimerRef.current = setInterval(() => {
      stepCounter += 1;

      if (stepCounter <= 4) {
        setCurrentStep(stepCounter);
      }
    }, 4500);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic: trimmedTopic }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Server error: ${response.status}`
        );
      }

      const data = await response.json();

      setCurrentStep(5);
      setResults(data);
    } catch (err) {
      setCurrentStep(null);
      setError(
        err.message || 'Unable to connect to the research server.'
      );
    } finally {
      if (stepTimerRef.current) {
        clearInterval(stepTimerRef.current);
        stepTimerRef.current = null;
      }

      setLoading(false);
    }
  };

  const suggestions = [
    'AI Market',
    'Stock Market',
    'Climate Change',
    'Electric Vehicles',
  ];

  return (
    <div className="app-container">

      {/* Navigation */}
      <nav className="navbar">
        <a href="/" className="brand">
          <span className="brand-icon">▱</span>
          <span>ResearchMind</span>
        </a>

        <div className="nav-links">
          <a href="#research" className="nav-link active">
            Research
          </a>
          <a href="#pipeline" className="nav-link">
            Workflow
          </a>
          <a href="#results" className="nav-link">
            Reports
          </a>
        </div>

        <div className="profile-avatar">R</div>
      </nav>

      {/* Hero */}
      <main>
        <section className="hero" id="research">
          <div className="hero-badge">
            <span className="status-dot" />
            MULTI-AGENT AI RESEARCH SYSTEM
          </div>

          <h1>
            AI <span>Research</span> Assistant
          </h1>

          <p className="hero-sub">
            An intelligent multi-agent system that searches, reads,
            writes, critiques, and refines in-depth research reports.
          </p>

          {/* Research Input */}
          <form className="research-form" onSubmit={handleSubmit}>
            <span className="input-icon">⌕</span>

            <input
              type="text"
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value);
                setError(null);
              }}
              placeholder="Enter a research topic..."
              disabled={loading}
            />

            <button
              type="submit"
              className="submit-button"
              disabled={loading}
            >
              {loading ? (
                <span className="spinner" />
              ) : (
                <span>→</span>
              )}
            </button>
          </form>

          {error && (
            <div className="error-banner">
              <span>⚠</span>
              {error}
            </div>
          )}

          {/* Suggested Topics */}
          <div className="suggestions">
            {suggestions.map((item) => (
              <button
                key={item}
                type="button"
                className="suggestion-chip"
                onClick={() => {
                  setTopic(item);
                  setError(null);
                }}
                disabled={loading}
              >
                {item}
              </button>
            ))}
          </div>
        </section>

        {/* Agent Workflow */}
        <section className="pipeline-section" id="pipeline">
          <div className="section-heading">
            <span>HOW IT WORKS</span>
            <h2>Research, powered by AI agents.</h2>
          </div>

          <div className="pipeline">
            {steps.map((step, index) => {
              const completed = currentStep > index + 1 ||
                currentStep === 5;

              const active = currentStep === index + 1;

              return (
                <React.Fragment key={step.title}>
                  <div
                    className={`pipeline-step ${
                      active ? 'step-active' : ''
                    } ${completed ? 'step-completed' : ''}`}
                  >
                    <div className="step-icon">
                      {step.icon}
                    </div>

                    <h3>{step.title}</h3>
                    <p>{step.description}</p>

                    {(completed || active) && (
                      <span className="step-status">
                        {completed ? '✓ Completed' : '● Processing'}
                      </span>
                    )}
                  </div>

                  {index !== steps.length - 1 && (
                    <div className="pipeline-arrow">→</div>
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {loading && (
            <p className="progress-text">
              Your research is being processed. This may take a few
              moments...
            </p>
          )}

          {results && !loading && (
            <p className="success-text">
              ✓ Research workflow completed successfully.
            </p>
          )}
        </section>

        {/* Research Results */}
        <section className="results-section" id="results">
          {results && <Results results={results} />}
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-brand">ResearchMind</div>
        <p>
          Built with LangGraph, LangChain, React & FastAPI
        </p>
        <span>Intelligent research. Better insights.</span>
      </footer>
    </div>
  );
}
