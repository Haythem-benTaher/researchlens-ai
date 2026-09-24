import { useRef, useState } from 'react'
import { uploadPaper } from '../api.js'

export default function UploadDropzone({ onUploaded }) {
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(null) // null | 0..1
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  async function handleFile(file) {
    if (!file) return
    if (file.type !== 'application/pdf') {
      setError('Only PDF files are accepted.')
      return
    }
    setError(null)
    setProgress(0)
    try {
      const paper = await uploadPaper(file, { onProgress: setProgress })
      onUploaded(paper)
    } catch (err) {
      setError(err.message || 'Upload failed.')
    } finally {
      setProgress(null)
    }
  }

  return (
    <div
      className={`dropzone${dragging ? ' dragging' : ''}`}
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        handleFile(e.dataTransfer.files?.[0])
      }}
    >
      <p>
        <strong>Drop a PDF here</strong>, or{' '}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault()
            inputRef.current?.click()
          }}
        >
          browse your files
        </a>
      </p>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      {progress !== null && (
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${Math.round(progress * 100)}%` }} />
        </div>
      )}
      {error && <p className="error-note" style={{ marginTop: 10 }}>{error}</p>}
    </div>
  )
}
