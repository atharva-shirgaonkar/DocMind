import { useRef, useState } from 'react'
import { uploadDocument } from '../api/documents.js'

const MAX_BYTES = 50 * 1024 * 1024

function validate(file) {
  const name = file.name.toLowerCase()
  if (!name.endsWith('.pdf') && !name.endsWith('.docx')) return `${file.name}: Choose a PDF or DOCX file.`
  if (file.size > MAX_BYTES) return `${file.name}: File must be 50 MB or smaller.`
  return ''
}

export default function UploadBox({ onUploaded }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [messages, setMessages] = useState([])
  const [error, setError] = useState('')

  async function handleFiles(fileList) {
    const files = Array.from(fileList || [])
    if (!files.length || uploading) return
    setError('')
    setMessages([])
    const nextMessages = []
    const invalid = files.map((file) => ({ file, issue: validate(file) })).filter((item) => item.issue)
    invalid.forEach(({ issue }) => nextMessages.push({ text: issue, kind: 'error' }))
    const valid = files.filter((file) => !validate(file))
    if (!valid.length) {
      setMessages(nextMessages)
      return
    }

    setUploading(true)
    for (const file of valid) {
      try {
        const { data, status } = await uploadDocument(file)
        nextMessages.push({
          text: status === 200
            ? 'Already uploaded - existing document shown.'
            : `${data?.original_filename || file.name} uploaded successfully. Processing will begin shortly.`,
          kind: status === 200 ? 'info' : 'success',
        })
      } catch (err) {
        nextMessages.push({ text: `${file.name}: ${err.message}`, kind: 'error' })
      }
    }
    setMessages(nextMessages)
    setUploading(false)
    await onUploaded()
    if (inputRef.current) inputRef.current.value = ''
  }

  function onDrop(event) {
    event.preventDefault()
    setDragging(false)
    handleFiles(event.dataTransfer.files)
  }

  return (
    <section
      onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
      onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false) }}
      onDrop={onDrop}
      className={`rounded-2xl border-2 border-dashed p-6 text-center transition sm:p-8 ${dragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-white'}`}
      aria-label="Upload documents"
    >
      <div className="mx-auto grid size-12 place-items-center rounded-xl bg-indigo-50 text-2xl text-indigo-600" aria-hidden="true">↑</div>
      <p className="mt-3 font-semibold text-slate-900">Drop PDF or DOCX files here</p>
      <p className="mt-1 text-sm text-slate-500">Up to 50 MB per file</p>
      <input ref={inputRef} type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" multiple className="sr-only" aria-label="Choose PDF or DOCX files" onChange={(event) => handleFiles(event.target.files)} />
      <button type="button" disabled={uploading} onClick={() => inputRef.current?.click()} className="mt-4 min-h-10 rounded-lg bg-indigo-600 px-4 text-sm font-semibold text-white hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-indigo-300">{uploading ? 'Uploading…' : 'Choose file'}</button>
      {uploading && <p className="mt-3 text-sm text-slate-500" role="status">Uploading files one at a time…</p>}
      {error && <p className="mt-3 text-sm text-red-700" role="alert">{error}</p>}
      {messages.length > 0 && <ul className="mx-auto mt-4 max-w-xl space-y-2 text-left" aria-live="polite">{messages.map((message, index) => <li key={`${message.text}-${index}`} className={`rounded-lg px-3 py-2 text-sm ${message.kind === 'error' ? 'bg-red-50 text-red-700' : message.kind === 'info' ? 'bg-indigo-50 text-indigo-800' : 'bg-green-50 text-green-800'}`}>{message.text}</li>)}</ul>}
    </section>
  )
}
