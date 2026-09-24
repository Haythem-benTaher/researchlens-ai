// Every function here talks to the FastAPI backend. In dev, Vite's proxy
// (vite.config.js) forwards these relative paths to http://localhost:8000;
// in production, serve the built frontend from the same origin as the API
// and these paths keep working unchanged.

async function handle(response) {
  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail || detail
    } catch {
      // response wasn't JSON — keep the status text
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function listPapers() {
  return handle(await fetch('/papers'))
}

export async function getPaper(paperId) {
  return handle(await fetch(`/papers/${paperId}`))
}

export async function uploadPaper(file, { onProgress } = {}) {
  const formData = new FormData()
  formData.append('file', file)

  // Plain fetch has no upload-progress event, so use XHR when the caller
  // wants progress (e.g. a large PDF); otherwise fetch is simpler.
  if (!onProgress) {
    return handle(await fetch('/papers/upload', { method: 'POST', body: formData }))
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/papers/upload')
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(e.loaded / e.total)
    }
    xhr.onload = () => {
      try {
        const body = JSON.parse(xhr.responseText)
        if (xhr.status >= 200 && xhr.status < 300) resolve(body)
        else reject(new Error(body.detail || xhr.statusText))
      } catch {
        reject(new Error('Upload failed'))
      }
    }
    xhr.onerror = () => reject(new Error('Upload failed'))
    xhr.send(formData)
  })
}

export async function deletePaper(paperId) {
  const res = await fetch(`/papers/${paperId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Could not delete paper')
}

export function paperFileUrl(paperId) {
  return `/papers/${paperId}/file`
}

export async function search(query, { topK = 5, paperId = null } = {}) {
  const params = new URLSearchParams({ q: query, top_k: String(topK) })
  if (paperId) params.set('paper_id', paperId)
  return handle(await fetch(`/search?${params.toString()}`))
}

export async function chat(question, { paperId = null, topK = null } = {}) {
  return handle(
    await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, paper_id: paperId, top_k: topK }),
    })
  )
}
