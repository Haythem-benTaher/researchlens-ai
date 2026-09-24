import { useEffect, useState } from 'react'
import UploadDropzone from '../components/UploadDropzone.jsx'
import PaperCard from '../components/PaperCard.jsx'
import { deletePaper, listPapers } from '../api.js'

export default function Library() {
  const [papers, setPapers] = useState(null) // null = loading
  const [error, setError] = useState(null)

  async function refresh() {
    try {
      setPapers(await listPapers())
    } catch (err) {
      setError(err.message || 'Could not load your library.')
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleDelete(paper) {
    if (!window.confirm(`Remove "${paper.title}" from your library?`)) return
    await deletePaper(paper.id)
    setPapers((prev) => prev.filter((p) => p.id !== paper.id))
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Library</h1>
          <p>Upload a paper to extract, chunk, and index it for search and chat.</p>
        </div>
      </div>

      <UploadDropzone onUploaded={(paper) => setPapers((prev) => [paper, ...(prev || [])])} />

      {error && <p className="error-note">{error}</p>}

      {papers === null && !error && <p style={{ color: 'var(--ink-muted)' }}>Loading your library…</p>}

      {papers && papers.length === 0 && (
        <div className="empty-state">
          <p>No papers yet. Drop a PDF above to get started.</p>
        </div>
      )}

      {papers && papers.length > 0 && (
        <div className="card-grid">
          {papers.map((paper) => (
            <PaperCard key={paper.id} paper={paper} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </>
  )
}
