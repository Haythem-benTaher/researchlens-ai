import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { deletePaper, getPaper, paperFileUrl } from '../api.js'

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

export default function PaperDetail() {
  const { paperId } = useParams()
  const [searchParams] = useSearchParams()
  const targetPage = searchParams.get('page')
  const navigate = useNavigate()
  const [paper, setPaper] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getPaper(paperId)
      .then(setPaper)
      .catch((err) => setError(err.message || 'Could not load this paper.'))
  }, [paperId])

  async function handleDelete() {
    if (!window.confirm(`Remove "${paper.title}" from your library?`)) return
    await deletePaper(paperId)
    navigate('/')
  }

  if (error) {
    return (
      <>
        <Link to="/">&larr; Back to library</Link>
        <p className="error-note" style={{ marginTop: 16 }}>{error}</p>
      </>
    )
  }

  if (!paper) {
    return <p style={{ color: 'var(--ink-muted)' }}>Loading…</p>
  }

  return (
    <>
      <div className="page-header">
        <div>
          <Link to="/">&larr; Back to library</Link>
          <h1 style={{ marginTop: 10 }}>{paper.title}</h1>
        </div>
      </div>

      <div className="paper-detail">
        <div className="pdf-frame-wrap">
          {paper.status === 'ready' ? (
            <iframe
              src={targetPage ? `${paperFileUrl(paper.id)}#page=${targetPage}` : paperFileUrl(paper.id)}
              title={paper.title}
            />
          ) : (
            <div style={{ padding: 24, color: 'var(--ink-muted)' }}>
              This paper isn't ready to view yet.
            </div>
          )}
        </div>

        <div className="detail-side">
          <div className="meta-block">
            <span className="label">Status</span>
            <span className={`status ${paper.status}`}>{paper.status}</span>
            {paper.error_message && <p className="error-note">{paper.error_message}</p>}

            <span className="label" style={{ marginTop: 8 }}>Pages</span>
            <span>{paper.page_count}</span>

            <span className="label" style={{ marginTop: 8 }}>Uploaded</span>
            <span>{formatDate(paper.uploaded_at)}</span>

            <span className="label" style={{ marginTop: 8 }}>Original filename</span>
            <span style={{ wordBreak: 'break-word' }}>{paper.original_filename}</span>
          </div>

          <Link
            className="btn btn-primary"
            to={`/chat?paper=${paper.id}`}
            style={{ justifyContent: 'center' }}
          >
            Ask about this paper
          </Link>
          <button className="btn btn-danger" onClick={handleDelete}>
            Remove from library
          </button>
        </div>
      </div>
    </>
  )
}
