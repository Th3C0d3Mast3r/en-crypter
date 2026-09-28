'use client'

import { useEffect, useRef, useState } from 'react'
import { ArrowRight, AudioLines, Boxes, ChevronRight, CircleHelp, FileArchive, FileText, FolderOpen, ImageIcon, LockKeyhole, Menu, Settings2, ShieldCheck, Sparkles, Terminal, Upload, X } from 'lucide-react'

const fallbackModules = [
  { name: 'Morse Audio', slug: 'morse', description: 'Text ↔ audio signal', icon: AudioLines, color: 'orange', tag: 'POPULAR', detail: 'Encode text as a downloadable .wav/.mp3 Morse signal.' },
  { name: 'Pixel Cipher', slug: 'pixels', description: 'Images ↔ hidden data', icon: ImageIcon, color: 'purple', tag: 'VISUAL', detail: 'Hide payloads inside image channels without changing the look.' },
  { name: 'Archive Vault', slug: 'archive', description: 'Files ↔ encrypted bundle', icon: FileArchive, color: 'cyan', tag: 'BATCH', detail: 'Wrap folders into a portable, encrypted archive.' },
  { name: 'Plain Text', slug: 'text', description: 'Text ↔ secure file', icon: FileText, color: 'lime', tag: 'FAST', detail: 'Turn notes into a compact encrypted text file.' },
  { name: 'Custom Module', slug: 'custom', description: 'Your next backend module', icon: Boxes, color: 'pink', tag: 'AUTO', detail: 'Any sub-directory with a manifest appears here automatically.' },
]

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Page() {
  const [modules, setModules] = useState(fallbackModules)
  const [selected, setSelected] = useState<(typeof fallbackModules)[number] | null>(null)
  const [mode, setMode] = useState<'encrypt' | 'decrypt'>('encrypt')
  const [source, setSource] = useState<'file' | 'folder'>('file')
  const [queued, setQueued] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [status, setStatus] = useState('Ready to process')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [filePreview, setFilePreview] = useState<string>('')
  const [saveResult, setSaveResult] = useState<{ message: string; outputDir: string; files: string[] } | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const canProcess = !!selectedFile && selected !== null

  useEffect(() => {
    let mounted = true

    fetch(`${API_BASE}/api/modules`)
      .then((res) => res.ok ? res.json() : [])
      .then((data) => {
        if (!mounted || !Array.isArray(data) || !data.length) return

        const nextModules = data.map((item: any, index: number) => ({
          name: item.name,
          slug: item.slug,
          description: item.description,
          icon: index % 2 === 0 ? AudioLines : ImageIcon,
          color: index % 2 === 0 ? 'orange' : 'purple',
          tag: 'API',
          detail: `Connected to ${item.backend} via the Python backend.`,
        }))

        setModules(nextModules)
        if (!selected) setSelected(nextModules[0])
      })
      .catch(() => undefined)

    return () => {
      mounted = false
    }
  }, [selected])

  const handleUpload = async () => {
    if (!selected || !selectedFile) {
      setStatus('Please pick a file before processing.')
      return
    }

    if (source === 'folder') {
      setStatus('Folder upload is not enabled yet. Please use single-file mode for manual testing.')
      return
    }

    setIsSubmitting(true)
    setQueued(true)
    setStatus(`Processing ${selected.name} via Python backend...`)
    setSaveResult(null)

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('module', selected.slug)
    formData.append('mode', mode)
    formData.append('source_type', source)

    try {
      const response = await fetch(`${API_BASE}/api/process`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data?.detail || data?.message || 'The backend rejected the request.')
      }

      const resultFiles = Array.isArray(data.files) ? data.files : []
      const outputDir = data.outputDir || 'Unknown output location'
      setSaveResult({
        message: data.message || 'Processing completed successfully.',
        outputDir,
        files: resultFiles,
      })
      setStatus(data.message || 'Processing completed successfully.')
      console.log('Process result:', data)
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Unknown processing error.')
    } finally {
      setIsSubmitting(false)
      setQueued(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><div className="brand-mark"><ShieldCheck size={20} strokeWidth={2.5} /></div><span>CRYPT<span className="brand-accent">CROSS</span></span></div>
        <div className="status"><span className="status-dot" /> LOCAL ENGINE <span className="status-divider">/</span> PYTHON BACKEND</div>
        <nav><button className="icon-button" aria-label="Help"><CircleHelp size={19} /></button><button className="icon-button" aria-label="Settings"><Settings2 size={19} /></button><button className="menu-button"><Menu size={18} /> MENU</button></nav>
      </header>

      <section className="hero"><div className="eyebrow"><Sparkles size={14} /> CROSS-TYPE ENCRYPTION STORAGE</div><h1>Make data <span>unrecognizable.</span></h1><p>Transform your files into entirely different types. <b>Local-first.</b> Private by design.</p><div className="hero-line"><span /><Terminal size={16} /><span /></div></section>

      <section className="workspace"><div className="section-heading"><div><p className="kicker">SELECT A MODULE</p><h2>Pick your weapon.</h2></div><div className="module-count">{modules.length} MODULES <span>·</span> LIVE API</div></div>
        <div className="module-grid">{modules.map((module, i) => { const Icon = module.icon; return <button key={module.slug} className={`module-card ${module.color} ${selected?.slug === module.slug ? 'active' : ''}`} onClick={() => { setSelected(module); setQueued(false) }}><div className="card-top"><span className="card-index">0{i + 1}</span><span className="tag">{module.tag}</span></div><div className="module-icon"><Icon size={30} strokeWidth={1.8} /></div><h3>{module.name}</h3><p>{module.description}</p><div className="card-arrow"><ArrowRight size={18} /></div></button> })}</div>
      </section>

      {selected && <section className="panel"><div className="panel-head"><div><p className="kicker">{selected.slug.toUpperCase()} / PROCESSOR</p><h2>{selected.name}</h2></div><button className="close-button" onClick={() => setSelected(null)} aria-label="Close processor"><X size={18} /></button></div><p className="panel-description">{selected.detail}</p><div className="mode-toggle"><button className={mode === 'encrypt' ? 'selected' : ''} onClick={() => setMode('encrypt')}><LockKeyhole size={16} /> ENCRYPT</button><button className={mode === 'decrypt' ? 'selected' : ''} onClick={() => setMode('decrypt')}><ShieldCheck size={16} /> DECRYPT</button></div><div className="source-row"><button className={`source-option ${source === 'file' ? 'selected' : ''}`} onClick={() => setSource('file')}><Upload size={21} /><span><b>Single file</b><small>Choose one input</small></span><ChevronRight size={16} /></button><button className={`source-option ${source === 'folder' ? 'selected' : ''}`} onClick={() => setSource('folder')}><FolderOpen size={21} /><span><b>Folder</b><small>Disabled for manual testing</small></span><ChevronRight size={16} /></button></div>

        <div className="upload-box">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.csv,.json,.bin,.md"
            onChange={(event) => {
              const file = event.target.files?.[0] || null
              setSelectedFile(file)

              if (file && file.size < 200000 && (file.type.startsWith('text/') || file.name.endsWith('.txt') || file.name.endsWith('.csv') || file.name.endsWith('.json') || file.name.endsWith('.md'))) {
                const reader = new FileReader()
                reader.onload = () => {
                  const text = typeof reader.result === 'string' ? reader.result : ''
                  setFilePreview(text.slice(0, 220))
                }
                reader.readAsText(file)
              } else {
                setFilePreview('')
              }
            }}
          />
          <button className="upload-button" onClick={() => fileInputRef.current?.click()}>
            {selectedFile ? `Selected: ${selectedFile.name}` : 'Choose file'}
          </button>
        </div>

        {filePreview && (
          <div className="preview-box">
            <div className="preview-title">FILE PREVIEW</div>
            <pre>{filePreview}</pre>
          </div>
        )}

        <button className="launch-button" disabled={isSubmitting || !canProcess} onClick={handleUpload}>
          {isSubmitting ? 'PROCESSING…' : queued ? 'READY — CONNECTING TO PYTHON' : `RUN ${source.toUpperCase()} & ${mode.toUpperCase()}`}
          <ArrowRight size={18} />
        </button>
        <div className="status-strip">{status}</div>

        {saveResult && (
          <div className="result-popup" role="alert">
            <div className="result-popup-header">✅ PROCESS COMPLETE</div>
            <p>{saveResult.message}</p>
            <div className="result-path">Saved to: {saveResult.outputDir}</div>
            {saveResult.files.length > 0 && (
              <ul>
                {saveResult.files.map((entry) => (
                  <li key={entry}>{entry}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>}

      <footer><span>CRYPT<span className="brand-accent">CROSS</span> // LOCAL TOOLKIT</span><span>NO CLOUD. NO TRACE. <ShieldCheck size={14} /></span></footer>
    </main>
  )
}

