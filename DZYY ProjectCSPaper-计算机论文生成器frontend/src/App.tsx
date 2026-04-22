import { useState, useEffect } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000/api/paper'

interface OutlineSection {
  id: string
  title: string
  level: number
  content_hint?: string
  word_count: number
}

interface Outline {
  paper_id: string
  title: string
  sections: OutlineSection[]
  total_words: number
  created_at: string
}

interface ContentSection {
  section_id: string
  title: string
  content: string
  word_count: number
  has_chart: boolean
  references: string[]
}

interface Content {
  paper_id: string
  title: string
  sections: ContentSection[]
  total_words: number
  references: string[]
  created_at: string
}

interface Reference {
  id: string
  type: string
  title: string
  authors: string[]
  year: number
  journal?: string
  doi?: string
}

interface PlagiarismReport {
  paper_id: string
  overall_rate: number
  section_rates: Record<string, number>
  suggestions: string[]
}

interface UserPaper {
  paper_id: string
  title: string
  paper_type: string
  status: string
  word_count: number
  created_at: string
}

type TabType = 'home' | 'generate' | 'outline' | 'content' | 'export' | 'history' | 'competition'

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('home')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [generating, setGenerating] = useState(false)

  const [paperType, setPaperType] = useState<'medical' | 'computer' | 'engineering' | 'liberal_arts'>('computer')
  const [thesisLevel, setThesisLevel] = useState<'bachelor' | 'master' | 'doctor'>('bachelor')
  const [title, setTitle] = useState('')
  const [subject, setSubject] = useState('')
  const [keywords, setKeywords] = useState('')
  const [requirements, setRequirements] = useState('')
  const [userId] = useState('default_user')

  const [outline, setOutline] = useState<Outline | null>(null)
  const [content, setContent] = useState<Content | null>(null)
  const [references, setReferences] = useState<Reference[]>([])
  const [plagiarismReport, setPlagiarismReport] = useState<PlagiarismReport | null>(null)
  const [history, setHistory] = useState<UserPaper[]>([])

  const [darkMode, setDarkMode] = useState(false)

  const typeColors = {
    computer: '#3B82F6',
    medical: '#10B981',
    engineering: '#F59E0B',
    liberal_arts: '#8B5CF6'
  }

  useEffect(() => {
    if (activeTab === 'history') loadHistory()
  }, [activeTab])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  const loadHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/papers/${userId}`)
      const data = await res.json()
      setHistory(data.papers || [])
    } catch (err) {
      console.error('Failed to load history')
    }
  }

  const handleGenerateOutline = async () => {
    if (!title.trim()) {
      setError('请输入论文标题')
      return
    }
    setLoading(true)
    setError(null)
    setProgress(10)
    try {
      const kwlist = keywords.split(/[,，、\s]+/).filter(k => k.trim())
      const res = await fetch(`${API_BASE}/generate/outline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper_type: paperType,
          title,
          subject: subject || '计算机科学与技术',
          keywords: kwlist.length >= 3 ? kwlist : [...kwlist, '研究', '分析'].slice(0, 3),
          user_id: userId,
          requirements
        })
      })
      if (!res.ok) throw new Error('Generation failed')
      setProgress(40)
      const data = await res.json()
      setOutline(data)
      setActiveTab('outline')
      setProgress(100)
    } catch (err: any) {
      setError(err.message || '生成大纲失败')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateContent = async () => {
    if (!outline) return
    setGenerating(true)
    setProgress(0)
    setError(null)
    try {
      const interval = setInterval(() => setProgress(p => Math.min(p + 5, 90)), 500)
      const res = await fetch(`${API_BASE}/generate/content?paper_id=${outline.paper_id}`, { method: 'POST' })
      clearInterval(interval)
      if (!res.ok) throw new Error('Generation failed')
      const data = await res.json()
      setContent(data)
      setProgress(100)
      setActiveTab('content')
    } catch (err: any) {
      setError(err.message || '生成正文失败')
    } finally {
      setGenerating(false)
    }
  }

  const handleGenerateFullPaper = async () => {
    if (!outline) return
    setGenerating(true)
    setProgress(0)
    try {
      await handleGenerateContent()
      const refRes = await fetch(`${API_BASE}/references/${outline.paper_id}`)
      if (refRes.ok) {
        const refData = await refRes.json()
        setReferences(refData.references || [])
      }
      const plRes = await fetch(`${API_BASE}/plagiarism/${outline.paper_id}`)
      if (plRes.ok) {
        const plData = await plRes.json()
        setPlagiarismReport(plData)
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleGetPlagiarismReport = async () => {
    if (!outline) return
    try {
      const res = await fetch(`${API_BASE}/plagiarism/${outline.paper_id}`)
      const data = await res.json()
      setPlagiarismReport(data)
    } catch (err) {
      setError('获取查重报告失败')
    }
  }

  const handleExport = async (format: 'docx' | 'pdf') => {
    if (!outline) return
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paper_id: outline.paper_id, format, include_toc: true, include_refs: true })
      })
      const data = await res.json()
      if (data.download_url) window.open(data.download_url, '_blank')
    } catch (err) {
      setError('导出失败')
    } finally {
      setLoading(false)
    }
  }

  const handleLoadPaper = async (paperId: string) => {
    try {
      const res = await fetch(`${API_BASE}/paper/${paperId}`)
      const data = await res.json()
      setOutline(data)
      setActiveTab('outline')
    } catch (err) {
      setError('加载论文失败')
    }
  }

  const handleDeletePaper = async (paperId: string) => {
    if (!confirm('确定要删除这篇论文吗？')) return
    try {
      await fetch(`${API_BASE}/paper/${paperId}`, { method: 'DELETE' })
      loadHistory()
    } catch (err) {
      setError('删除失败')
    }
  }

  const renderHome = () => (
    <div className="home">
      <div className="hero-section">
        <h1>CSPaper 论文生成系统</h1>
        <p className="subtitle">全自主智能论文生成 | 支持计算机/医学/工科/文科</p>
        <div className="quick-actions">
          <button className="btn btn-primary btn-large" onClick={() => setActiveTab('generate')}>开始生成论文</button>
          <button className="btn btn-secondary btn-large" onClick={() => setActiveTab('competition')}>竞赛申报模式</button>
        </div>
      </div>
      <div className="features-grid">
        <div className="feature-card"><div className="feature-icon">📋</div><h3>智能大纲</h3><p>符合学校规范的论文大纲结构</p></div>
        <div className="feature-card"><div className="feature-icon">✍️</div><h3>自动写作</h3><p>AI续写各章节内容</p></div>
        <div className="feature-card"><div className="feature-icon">📊</div><h3>图表生成</h3><p>数据可视化图表自动插入</p></div>
        <div className="feature-card"><div className="feature-icon">📄</div><h3>格式导出</h3><p>DOCX/PDF符合学校格式</p></div>
        <div className="feature-card"><div className="feature-icon">🔍</div><h3>查重报告</h3><p>模拟知网/万方查重</p></div>
        <div className="feature-card"><div className="feature-icon">📚</div><h3>参考文献</h3><p>GB/T 7714标准格式化</p></div>
      </div>
    </div>
  )

  const renderGenerate = () => (
    <div className="generate-page">
      <div className="page-header"><h2>创建新论文</h2></div>
      <div className="form-section">
        <div className="form-group">
          <label>论文类型</label>
          <div className="type-selector">
            {(['computer', 'medical', 'engineering', 'liberal_arts'] as const).map(type => (
              <button key={type} className={`type-btn ${paperType === type ? 'active' : ''}`} onClick={() => setPaperType(type)}>
                {type === 'computer' && '💻'}{type === 'medical' && '🏥'}{type === 'engineering' && '⚙️'}{type === 'liberal_arts' && '📖'}
                <span>{type === 'computer' ? '计算机' : type === 'medical' ? '医学' : type === 'engineering' ? '工科' : '文科'}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="form-group">
          <label>学位层次</label>
          <div className="level-selector">
            {(['bachelor', 'master', 'doctor'] as const).map(level => (
              <button key={level} className={`level-btn ${thesisLevel === level ? 'active' : ''}`} onClick={() => setThesisLevel(level)}>
                {level === 'bachelor' ? '本科' : level === 'master' ? '硕士' : '博士'}
              </button>
            ))}
          </div>
        </div>
        <div className="form-group">
          <label>论文标题 *</label>
          <input type="text" className="form-input" placeholder="请输入论文标题" value={title} onChange={e => setTitle(e.target.value)} />
        </div>
        <div className="form-group">
          <label>专业方向</label>
          <input type="text" className="form-input" placeholder="如：计算机科学与技术" value={subject} onChange={e => setSubject(e.target.value)} />
        </div>
        <div className="form-group">
          <label>关键词（用逗号分隔，至少3个）</label>
          <input type="text" className="form-input" placeholder="如：深度学习, 图像识别, 神经网络" value={keywords} onChange={e => setKeywords(e.target.value)} />
        </div>
        <div className="form-group">
          <label>特殊要求</label>
          <textarea className="form-textarea" placeholder="如有特殊要求请在此说明" value={requirements} onChange={e => setRequirements(e.target.value)} />
        </div>
        {error && <div className="error-message">{error}</div>}
        <div className="form-actions">
          <button className="btn btn-primary btn-large" onClick={handleGenerateOutline} disabled={loading}>
            {loading ? '生成中...' : '生成论文大纲'}
          </button>
        </div>
      </div>
    </div>
  )

  const renderOutline = () => (
    <div className="outline-page">
      <div className="page-header">
        <div><h2>论文大纲</h2><p className="paper-title">{outline?.title}</p></div>
        <button className="btn btn-secondary" onClick={() => setActiveTab('generate')}>重新编辑</button>
      </div>
      {generating && <div className="progress-bar-container"><div className="progress-bar" style={{ width: `${progress}%` }}></div><span>生成进度: {progress}%</span></div>}
      <div className="outline-stats">
        <div className="stat-badge"><span>📄</span><span>{outline?.sections.length} 章节</span></div>
        <div className="stat-badge"><span>📝</span><span>约 {outline?.total_words} 字</span></div>
      </div>
      <div className="outline-tree">
        {outline?.sections.map((section, index) => (
          <div key={section.id} className={`outline-item level-${section.level}`}>
            <div className="outline-item-content">
              <span className="outline-title">{section.title}</span>
              <span className="outline-words">约{section.word_count}字</span>
            </div>
          </div>
        ))}
      </div>
      <div className="outline-actions">
        <button className="btn btn-primary btn-large" onClick={handleGenerateFullPaper} disabled={generating}>
          {generating ? `生成中... ${progress}%` : '一键生成完整论文'}
        </button>
        <div className="action-secondary">
          <button className="btn btn-secondary" onClick={handleGenerateContent} disabled={generating}>生成正文</button>
          <button className="btn btn-secondary" onClick={handleGetPlagiarismReport}>查重报告</button>
        </div>
      </div>
    </div>
  )

  const renderContent = () => (
    <div className="content-page">
      <div className="page-header">
        <div><h2>论文内容</h2><p className="paper-title">{content?.title}</p></div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => setActiveTab('outline')}>查看大纲</button>
          <button className="btn btn-primary" onClick={() => setActiveTab('export')}>导出论文</button>
        </div>
      </div>
      <div className="content-stats">
        <div className="stat-badge primary"><span>{content?.total_words} 字</span></div>
        <div className="stat-badge"><span>{content?.sections.length} 章节</span></div>
      </div>
      <div className="content-sections">
        {content?.sections.map((section) => (
          <div key={section.section_id} className="content-section">
            <div className="section-header"><h3>{section.title}</h3><span className="word-count">{section.word_count} 字</span></div>
            <div className="section-content">{section.content.split('\n').map((para, i) => para.trim() && <p key={i}>{para}</p>)}</div>
          </div>
        ))}
      </div>
    </div>
  )

  const renderExport = () => (
    <div className="export-page">
      <div className="page-header"><h2>导出论文</h2></div>
      <div className="export-options">
        <div className="export-card"><h3>Word 文档</h3><p>.docx 格式</p><button className="btn btn-primary" onClick={() => handleExport('docx')} disabled={loading}>导出 DOCX</button></div>
        <div className="export-card"><h3>PDF 文档</h3><p>.pdf 格式</p><button className="btn btn-secondary" onClick={() => handleExport('pdf')} disabled={loading}>导出 PDF</button></div>
      </div>
      {plagiarismReport && (
        <div className="plagiarism-section">
          <h3>查重报告</h3>
          <div className="rate-circle"><span>{plagiarismReport.overall_rate}%</span></div>
          <div className="suggestions">
            {plagiarismReport.suggestions.map((s, i) => <li key={i}>{s}</li>)}
          </div>
        </div>
      )}
    </div>
  )

  const renderHistory = () => (
    <div className="history-page">
      <div className="page-header"><h2>历史论文</h2><button className="btn btn-secondary" onClick={loadHistory}>刷新</button></div>
      {history.length === 0 ? (
        <div className="empty-state"><p>暂无历史论文</p><button className="btn btn-primary" onClick={() => setActiveTab('generate')}>开始创建</button></div>
      ) : (
        <div className="history-list">
          {history.map(paper => (
            <div key={paper.paper_id} className="history-item">
              <h3>{paper.title}</h3>
              <div className="history-meta"><span>{paper.word_count} 字</span><span>{new Date(paper.created_at).toLocaleDateString()}</span></div>
              <div className="history-actions">
                <button className="btn btn-small btn-primary" onClick={() => handleLoadPaper(paper.paper_id)}>继续编辑</button>
                <button className="btn btn-small btn-danger" onClick={() => handleDeletePaper(paper.paper_id)}>删除</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  const renderCompetition = () => (
    <div className="competition-page">
      <div className="page-header"><h2>竞赛申报书生成</h2><p>一键生成计算机设计大赛参赛材料</p></div>
      <div className="competition-templates">
        <div className="template-card"><h3>技术报告</h3><button className="btn btn-primary">生成</button></div>
        <div className="template-card"><h3>演讲稿</h3><button className="btn btn-primary">生成</button></div>
        <div className="template-card"><h3>申报书</h3><button className="btn btn-primary">生成</button></div>
        <div className="template-card"><h3>展示内容</h3><button className="btn btn-primary">生成</button></div>
      </div>
    </div>
  )

  return (
    <div className={`app ${darkMode ? 'dark' : 'light'}`}>
      <nav className="navbar">
        <div className="nav-brand" onClick={() => setActiveTab('home')}>CSPaper</div>
        <div className="nav-links">
          <button className={`nav-link ${activeTab === 'home' ? 'active' : ''}`} onClick={() => setActiveTab('home')}>首页</button>
          <button className={`nav-link ${activeTab === 'generate' ? 'active' : ''}`} onClick={() => setActiveTab('generate')}>生成</button>
          <button className={`nav-link ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>历史</button>
          <button className={`nav-link ${activeTab === 'competition' ? 'active' : ''}`} onClick={() => setActiveTab('competition')}>竞赛</button>
        </div>
        <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>{darkMode ? '☀️' : '🌙'}</button>
      </nav>
      <main className="main-content">
        {activeTab === 'home' && renderHome()}
        {activeTab === 'generate' && renderGenerate()}
        {activeTab === 'outline' && renderOutline()}
        {activeTab === 'content' && renderContent()}
        {activeTab === 'export' && renderExport()}
        {activeTab === 'history' && renderHistory()}
        {activeTab === 'competition' && renderCompetition()}
      </main>
      <footer className="footer"><p>CSPaper 论文生成系统 v2.0</p></footer>
    </div>
  )
}

export default App
