import { Link } from 'react-router-dom'

export default function CitationChip({ citation }) {
  return (
    <Link
      className="citation-chip"
      to={`/papers/${citation.paper_id}?page=${citation.page_number}`}
      title={citation.snippet}
    >
      {citation.paper_title}, p. {citation.page_number}
    </Link>
  )
}
