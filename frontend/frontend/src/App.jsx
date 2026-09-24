import { NavLink, Route, Routes } from 'react-router-dom'
import Library from './pages/Library.jsx'
import PaperDetail from './pages/PaperDetail.jsx'
import Chat from './pages/Chat.jsx'

export default function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="wordmark">
          <span className="mark">ResearchLens</span>
          <span className="sub">read, search, ask</span>
        </div>
        <nav className="nav">
          <NavLink to="/" className={({ isActive }) => (isActive ? 'active' : '')} end>
            Library
          </NavLink>
          <NavLink to="/chat" className={({ isActive }) => (isActive ? 'active' : '')}>
            Chat
          </NavLink>
        </nav>
      </aside>

      <main className="main">
        <Routes>
          <Route path="/" element={<Library />} />
          <Route path="/papers/:paperId" element={<PaperDetail />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </main>
    </div>
  )
}
