import { useState, useEffect, useRef } from "react"
import axios from "axios"

const API = "http://13.60.202.50:8000"
const ALLOWED = [".pdf", ".pptx", ".xlsx"]

function getExt(filename) {
  return filename.slice(filename.lastIndexOf(".")).toLowerCase()
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric"
  })
}

export default function Projects({ onBack, onSelectProject }) {
  const [projects, setProjects]         = useState([])
  const [loading, setLoading]           = useState(true)
  const [view, setView]                 = useState("list")       // "list" | "detail"
  const [activeProject, setActiveProject] = useState(null)
  const [showCreate, setShowCreate]     = useState(false)
  const [showRename, setShowRename]     = useState(false)
  const [newName, setNewName]           = useState("")
  const [newDesc, setNewDesc]           = useState("")
  const [renameVal, setRenameVal]       = useState("")
  const [uploading, setUploading]       = useState(false)
  const [toast, setToast]               = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => { fetchProjects() }, [])

  const showToast = (msg, type = "success") => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API}/projects`)
      setProjects(res.data.projects || [])
    } catch {
      showToast("Failed to load projects.", "error")
    }
    setLoading(false)
  }

  const createProject = async () => {
    if (!newName.trim()) return
    try {
      const res = await axios.post(`${API}/projects`, {
        name: newName.trim(),
        description: newDesc.trim()
      })
      setProjects(prev => [...prev, res.data])
      setShowCreate(false)
      setNewName("")
      setNewDesc("")
      showToast(`Project "${res.data.name}" created!`)
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to create project.", "error")
    }
  }

  const renameProject = async () => {
    if (!renameVal.trim()) return
    try {
      const res = await axios.put(`${API}/projects/${activeProject.id}`, {
        name: renameVal.trim()
      })
      setProjects(prev => prev.map(p => p.id === activeProject.id ? res.data : p))
      setActiveProject(res.data)
      setShowRename(false)
      showToast("Project renamed!")
    } catch {
      showToast("Failed to rename project.", "error")
    }
  }

  const deleteProject = async (projectId, projectName) => {
    if (!confirm(`Delete project "${projectName}"? This cannot be undone.`)) return
    try {
      await axios.delete(`${API}/projects/${projectId}`)
      setProjects(prev => prev.filter(p => p.id !== projectId))
      if (view === "detail") setView("list")
      showToast(`Project "${projectName}" deleted.`)
    } catch {
      showToast("Failed to delete project.", "error")
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const ext = getExt(file.name)
    if (!ALLOWED.includes(ext)) {
      showToast(`"${ext}" is not supported. Please upload PDF, PPTX, or XLSX.`, "error")
      e.target.value = ""
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await axios.post(
        `${API}/projects/${activeProject.id}/upload`,
        formData
      )
      setActiveProject(res.data.project)
      setProjects(prev => prev.map(p =>
        p.id === activeProject.id ? res.data.project : p
      ))
      showToast(`"${file.name}" uploaded and indexed!`)
    } catch (err) {
      showToast(err.response?.data?.detail || "Upload failed.", "error")
    }
    setUploading(false)
    e.target.value = ""
  }

  const deleteDoc = async (filename) => {
    if (!confirm(`Delete "${filename}"?`)) return
    try {
      await axios.delete(`${API}/projects/${activeProject.id}/docs/${filename}`)
      const updated = {
        ...activeProject,
        docs: activeProject.docs.filter(d => d !== filename),
        doc_count: activeProject.doc_count - 1
      }
      setActiveProject(updated)
      setProjects(prev => prev.map(p =>
        p.id === activeProject.id ? updated : p
      ))
      showToast(`"${filename}" deleted.`)
    } catch {
      showToast("Failed to delete file.", "error")
    }
  }

  const openProject = (project) => {
    setActiveProject(project)
    setView("detail")
  }

  const fileIcon = (filename) => {
    const ext = getExt(filename)
    if (ext === ".pdf")  return "PDF"
    if (ext === ".pptx") return "PPT"
    if (ext === ".xlsx") return "XLS"
    return "DOC"
  }

  const fileColor = (filename) => {
    const ext = getExt(filename)
    if (ext === ".pdf")  return { bg: "#FCEBEB", color: "#A32D2D", dark: "#501313", darkColor: "#F09595" }
    if (ext === ".pptx") return { bg: "#FAEEDA", color: "#854F0B", dark: "#412402", darkColor: "#FAC775" }
    if (ext === ".xlsx") return { bg: "#EAF3DE", color: "#3B6D11", dark: "#173404", darkColor: "#C0DD97" }
    return { bg: "#E6F1FB", color: "#0C447C", dark: "#042C53", darkColor: "#B5D4F4" }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0d0e12", color: "#d1d2d3", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>

      {/* ── Toast ── */}
      {toast && (
        <div style={{
          position: "fixed", top: "20px", right: "20px", zIndex: 1000,
          background: toast.type === "error" ? "#A32D2D" : "#0F6E56",
          color: "#fff", padding: "10px 18px", borderRadius: "8px",
          fontSize: "13px", fontWeight: "500", boxShadow: "0 4px 12px rgba(0,0,0,0.4)"
        }}>
          {toast.msg}
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ padding: "16px 28px", borderBottom: "1px solid #1e2029", display: "flex", alignItems: "center", gap: "14px", background: "#111218", flexShrink: 0 }}>
        <button
          onClick={onBack}
          style={{ background: "none", border: "1px solid #2c2d30", color: "#9b9fa4", borderRadius: "6px", padding: "6px 12px", cursor: "pointer", fontSize: "13px" }}
        >
          ← Back
        </button>
        {view === "detail" && (
          <button
            onClick={() => setView("list")}
            style={{ background: "none", border: "1px solid #2c2d30", color: "#9b9fa4", borderRadius: "6px", padding: "6px 12px", cursor: "pointer", fontSize: "13px" }}
          >
            All Projects
          </button>
        )}
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "18px", fontWeight: "600", color: "#f9fafb" }}>
            {view === "list" ? "Projects" : activeProject?.name}
          </div>
          <div style={{ fontSize: "12px", color: "#4b5563", marginTop: "2px" }}>
            {view === "list"
              ? `${projects.length} project${projects.length !== 1 ? "s" : ""}`
              : activeProject?.description || "No description"
            }
          </div>
        </div>

        {view === "list" && (
          <button
            onClick={() => setShowCreate(true)}
            style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "600", cursor: "pointer" }}
          >
            + New Project
          </button>
        )}

        {view === "detail" && (
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={() => { setRenameVal(activeProject.name); setShowRename(true) }}
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid #2c2d30", color: "#d1d2d3", borderRadius: "8px", padding: "8px 16px", fontSize: "13px", cursor: "pointer" }}
            >
              Rename
            </button>
            <button
              onClick={() => onSelectProject && onSelectProject(activeProject)}
              style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", border: "none", borderRadius: "8px", padding: "8px 16px", fontSize: "13px", fontWeight: "600", cursor: "pointer" }}
            >
              Ask this Project
            </button>
            <button
              onClick={() => deleteProject(activeProject.id, activeProject.name)}
              style={{ background: "rgba(162,45,45,0.15)", border: "1px solid rgba(162,45,45,0.3)", color: "#F09595", borderRadius: "8px", padding: "8px 14px", fontSize: "13px", cursor: "pointer" }}
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {/* ── Body ── */}
      <div style={{ flex: 1, overflow: "auto", padding: "28px" }}>

        {/* ── Projects List View ── */}
        {view === "list" && (
          <>
            {loading ? (
              <div style={{ color: "#4b5563", fontSize: "14px" }}>Loading projects...</div>
            ) : projects.length === 0 ? (
              <div style={{ textAlign: "center", padding: "80px 20px" }}>
                <div style={{ fontSize: "40px", marginBottom: "16px" }}>📁</div>
                <div style={{ fontSize: "18px", fontWeight: "600", color: "#f9fafb", marginBottom: "8px" }}>No projects yet</div>
                <div style={{ fontSize: "14px", color: "#4b5563", marginBottom: "24px" }}>Create your first project to start uploading documents.</div>
                <button
                  onClick={() => setShowCreate(true)}
                  style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", border: "none", borderRadius: "8px", padding: "10px 24px", fontSize: "14px", fontWeight: "600", cursor: "pointer" }}
                >
                  Create Project
                </button>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "16px" }}>
                {projects.map(project => (
                  <div
                    key={project.id}
                    onClick={() => openProject(project)}
                    style={{ background: "#161720", border: "1px solid #1e2029", borderRadius: "12px", padding: "20px", cursor: "pointer", transition: "border-color 0.2s, transform 0.15s" }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = "#4f46e5"; e.currentTarget.style.transform = "translateY(-2px)" }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = "#1e2029"; e.currentTarget.style.transform = "translateY(0)" }}
                  >
                    <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px", marginBottom: "14px", color: "#fff", fontWeight: "700" }}>
                      {project.name.charAt(0).toUpperCase()}
                    </div>
                    <div style={{ fontSize: "15px", fontWeight: "600", color: "#f9fafb", marginBottom: "4px" }}>{project.name}</div>
                    <div style={{ fontSize: "12px", color: "#4b5563", marginBottom: "14px", lineHeight: "1.5", minHeight: "18px" }}>
                      {project.description || "No description"}
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "12px", color: "#6b7280" }}>
                        {project.doc_count} doc{project.doc_count !== 1 ? "s" : ""}
                      </span>
                      <span style={{ fontSize: "11px", color: "#374151" }}>
                        {formatDate(project.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* ── Project Detail View ── */}
        {view === "detail" && activeProject && (
          <div style={{ maxWidth: "800px" }}>

            {/* Upload zone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              style={{ border: "2px dashed #1e2029", borderRadius: "12px", padding: "32px", textAlign: "center", cursor: "pointer", marginBottom: "24px", transition: "border-color 0.2s, background 0.2s" }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "#4f46e5"; e.currentTarget.style.background = "rgba(99,102,241,0.05)" }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "#1e2029"; e.currentTarget.style.background = "transparent" }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.pptx,.xlsx"
                style={{ display: "none" }}
                onChange={handleFileUpload}
              />
              {uploading ? (
                <div style={{ color: "#818cf8", fontSize: "14px", fontWeight: "500" }}>Uploading and indexing...</div>
              ) : (
                <>
                  <div style={{ fontSize: "28px", marginBottom: "10px" }}>+</div>
                  <div style={{ fontSize: "14px", color: "#9ca3af", marginBottom: "4px" }}>
                    Click to upload documents
                  </div>
                  <div style={{ fontSize: "12px", color: "#4b5563" }}>
                    Supported: PDF, PPTX, XLSX
                  </div>
                </>
              )}
            </div>

            {/* Documents list */}
            {activeProject.docs.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px", color: "#4b5563", fontSize: "14px" }}>
                No documents yet. Upload your first file above.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div style={{ fontSize: "12px", color: "#4b5563", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "4px" }}>
                  {activeProject.docs.length} Document{activeProject.docs.length !== 1 ? "s" : ""}
                </div>
                {activeProject.docs.map(filename => {
                  const fc = fileColor(filename)
                  return (
                    <div
                      key={filename}
                      style={{ background: "#161720", border: "1px solid #1e2029", borderRadius: "10px", padding: "12px 16px", display: "flex", alignItems: "center", gap: "12px" }}
                    >
                      <div style={{ background: fc.bg, color: fc.color, fontSize: "10px", fontWeight: "700", padding: "4px 6px", borderRadius: "4px", flexShrink: 0 }}>
                        {fileIcon(filename)}
                      </div>
                      <div style={{ flex: 1, fontSize: "13px", color: "#d1d2d3", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {filename}
                      </div>
                      <button
                        onClick={() => deleteDoc(filename)}
                        style={{ background: "none", border: "none", color: "#4b5563", cursor: "pointer", fontSize: "16px", padding: "0 4px", flexShrink: 0, lineHeight: 1 }}
                        title="Delete file"
                      >
                        ×
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Create Project Modal ── */}
      {showCreate && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 999 }}>
          <div style={{ background: "#161720", border: "1px solid #2c2d30", borderRadius: "16px", padding: "28px", width: "420px", maxWidth: "90vw" }}>
            <div style={{ fontSize: "17px", fontWeight: "600", color: "#f9fafb", marginBottom: "20px" }}>Create New Project</div>

            <div style={{ marginBottom: "14px" }}>
              <label style={{ fontSize: "12px", color: "#6b7280", display: "block", marginBottom: "6px", fontWeight: "500" }}>Project Name *</label>
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === "Enter" && createProject()}
                placeholder="e.g. HR Policies"
                autoFocus
                style={{ width: "100%", background: "#0d0e12", border: "1px solid #2c2d30", borderRadius: "8px", padding: "10px 12px", color: "#d1d2d3", fontSize: "14px", outline: "none", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ fontSize: "12px", color: "#6b7280", display: "block", marginBottom: "6px", fontWeight: "500" }}>Description (optional)</label>
              <input
                value={newDesc}
                onChange={e => setNewDesc(e.target.value)}
                placeholder="e.g. All HR and company policy documents"
                style={{ width: "100%", background: "#0d0e12", border: "1px solid #2c2d30", borderRadius: "8px", padding: "10px 12px", color: "#d1d2d3", fontSize: "14px", outline: "none", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                onClick={() => { setShowCreate(false); setNewName(""); setNewDesc("") }}
                style={{ background: "none", border: "1px solid #2c2d30", color: "#9b9fa4", borderRadius: "8px", padding: "9px 18px", fontSize: "13px", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                onClick={createProject}
                disabled={!newName.trim()}
                style={{ background: newName.trim() ? "linear-gradient(135deg,#6366f1,#8b5cf6)" : "#374151", color: "#fff", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "600", cursor: newName.trim() ? "pointer" : "not-allowed" }}
              >
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Rename Modal ── */}
      {showRename && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 999 }}>
          <div style={{ background: "#161720", border: "1px solid #2c2d30", borderRadius: "16px", padding: "28px", width: "380px", maxWidth: "90vw" }}>
            <div style={{ fontSize: "17px", fontWeight: "600", color: "#f9fafb", marginBottom: "20px" }}>Rename Project</div>
            <input
              value={renameVal}
              onChange={e => setRenameVal(e.target.value)}
              onKeyDown={e => e.key === "Enter" && renameProject()}
              autoFocus
              style={{ width: "100%", background: "#0d0e12", border: "1px solid #2c2d30", borderRadius: "8px", padding: "10px 12px", color: "#d1d2d3", fontSize: "14px", outline: "none", boxSizing: "border-box", marginBottom: "20px" }}
            />
            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                onClick={() => setShowRename(false)}
                style={{ background: "none", border: "1px solid #2c2d30", color: "#9b9fa4", borderRadius: "8px", padding: "9px 18px", fontSize: "13px", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                onClick={renameProject}
                style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", border: "none", borderRadius: "8px", padding: "9px 20px", fontSize: "13px", fontWeight: "600", cursor: "pointer" }}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}