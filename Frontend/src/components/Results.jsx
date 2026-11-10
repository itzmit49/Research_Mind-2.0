
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function Results({ results }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [readerOpen, setReaderOpen] = useState(false);

  if (!results) return null;

  const handleDownload = () => {
    if (!results.writer) return;

    const blob = new Blob([results.writer], {
      type: 'text/markdown;charset=utf-8;',
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.href = url;
    link.download = `research_report_${Date.now()}.md`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  const markdownComponents = {
    table: ({ children }) => (
      <div className="markdown-table-wrapper">
        <table>{children}</table>
      </div>
    ),
  };

  const renderMarkdown = (content) => (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={markdownComponents}
    >
      {content || ''}
    </ReactMarkdown>
  );

  return (
    <div className="results-section">

      <div className="divider"></div>

      <div className="section-heading">
        <span>Results</span>
      </div>

      {/* Search Agent Output */}
      {results.search && (
        <div className="custom-expander">
          <div
            className="expander-header"
            onClick={() => setSearchOpen(!searchOpen)}
          >
            <span>🔍 Search Results (raw)</span>
            <span className={`expander-arrow ${searchOpen ? 'open' : ''}`}>
              ▼
            </span>
          </div>

          {searchOpen && (
            <div className="expander-body">
              <div className="result-panel-title">
                Search Agent Output
              </div>
              <div className="result-content">
                {results.search}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Reader Agent Output */}
      {results.reader && (
        <div className="custom-expander">
          <div
            className="expander-header"
            onClick={() => setReaderOpen(!readerOpen)}
          >
            <span>📄 Scraped Content (raw)</span>
            <span className={`expander-arrow ${readerOpen ? 'open' : ''}`}>
              ▼
            </span>
          </div>

          {readerOpen && (
            <div className="expander-body">
              <div className="result-panel-title">
                Reader Agent Output
              </div>
              <div className="result-content">
                {results.reader}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Final Research Report */}
      {results.writer && (
        <div className="report-panel">

          <div className="panel-header-row panel-border-orange">
            <span className="panel-label orange">
              📝 Final Research Report
            </span>

            <button
              className="btn-download"
              onClick={handleDownload}
            >
              ⬇ Download Report (.md)
            </button>
          </div>

          <div className="markdown-body">
            {renderMarkdown(results.writer)}
          </div>

        </div>
      )}

      {/* Critic Feedback */}
      {results.critic && (
        <div className="feedback-panel">

          <div className="panel-header-row panel-border-green">
            <span className="panel-label green">
              🧐 Critic Feedback
            </span>
          </div>

          <div className="markdown-body">
            {renderMarkdown(results.critic)}
          </div>

        </div>
      )}

    </div>
  );
}
