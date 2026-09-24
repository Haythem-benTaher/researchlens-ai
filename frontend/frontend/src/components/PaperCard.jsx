import { Link } from 'react-router-dom'

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

export default function PaperCard({ paper, onDelete }) {
  return (
    <div className="index-card">
      <h3>
        <Link className="title-link" to={`/papers/${paper.id}`}>
          {paper.title}
        </Link>
      </h3>
      <div className="meta">
        <span>{paper.page_count} {paper.page_count === 1 ? 'page' : 'pages'}</span>
        <span>Uploaded {formatDate(paper.uploaded_at)}</span>
      </div>
      {paper.status === 'failed' && paper.error_message && (
        <p className="error-note">{paper.error_message}</p>
      )}
      <div className="row">
        <span className={`status ${paper.status}`}>{paper.status}</span>
        <button className="btn-quiet" onClick={() => onDelete(paper)}>
          Remove
        </button>
      </div>
    </div>
  )
}
