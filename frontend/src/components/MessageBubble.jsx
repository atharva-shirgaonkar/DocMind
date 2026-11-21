import { useState } from 'react'
import SourceCard from './SourceCard.jsx'

function AnswerText({ text, onCitation }) {
  const parts = text.split(/(\[(?:\d+)(?:\]\[\d+)*\])/g)
  return <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{parts.map((part, index) => {
    if (/^\[\d+(?:\]\[\d+)*\]$/.test(part)) {
      const numbers = [...part.matchAll(/\d+/g)].map((match) => Number(match[0]))
      return <span key={index} className="inline-flex gap-1 align-middle">{numbers.map((number) => <button key={number} type="button" onClick={() => onCitation(number)} aria-label={`Show source ${number}`} className="mx-0.5 rounded bg-indigo-100 px-1.5 py-0.5 text-xs font-bold text-indigo-700 hover:bg-indigo-200 focus-visible:outline-2 focus-visible:outline-indigo-600">{number}</button>)}</span>
    }
    return <span key={index}>{part}</span>
  })}</p>
}

export default function MessageBubble({ message, onRetry, onCitation }) {
  const [showSources, setShowSources] = useState(true)
  const [copied, setCopied] = useState(false)
  if (message.role === 'error') {
    return <div className="ml-auto max-w-2xl rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
      <p>{message.text}</p>
      <button type="button" onClick={onRetry} className="mt-2 rounded font-semibold underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-red-700">Retry</button>
    </div>
  }
  if (message.role === 'user') return <div className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-indigo-600 px-4 py-3 text-sm leading-6 text-white shadow-sm">{message.text}</div>
  if (message.role === 'typing') return <div role="status" className="w-fit rounded-2xl bg-white px-4 py-3 text-sm text-slate-500 shadow-sm"><span className="animate-pulse">DocMind is thinking…</span></div>
  if (message.role === 'search') return <div className="max-w-3xl rounded-2xl rounded-bl-md bg-white p-4 shadow-sm sm:p-5">
    <p className="mb-3 text-sm font-semibold text-slate-800">{message.results.length ? `Found ${message.results.length} matching chunks` : 'No matching chunks found.'}</p>
    <div className="space-y-3">{message.results.map((source, index) => <SourceCard key={source.chunk_id || index} source={{ ...source, citation_number: index + 1, snippet: source.content }} onHighlight={onCitation} />)}</div>
  </div>

  const neutral = message.answer === "I couldn't find the answer in the uploaded documents."
  return <div className="max-w-3xl rounded-2xl rounded-bl-md bg-white p-4 shadow-sm sm:p-5">
    <div className="flex items-start justify-between gap-3">
      {neutral ? <p className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-600">{message.answer}</p> : <AnswerText text={message.answer} onCitation={onCitation} />}
      <button type="button" onClick={async () => { await navigator.clipboard.writeText(message.answer); setCopied(true); window.setTimeout(() => setCopied(false), 1500) }} className="shrink-0 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-indigo-600">{copied ? 'Copied' : 'Copy'}</button>
    </div>
    {message.sources?.length > 0 && <div className="mt-4 border-t border-slate-100 pt-3">
      <button type="button" aria-expanded={showSources} onClick={() => setShowSources((value) => !value)} className="rounded text-sm font-semibold text-slate-700 hover:text-indigo-700 focus-visible:outline-2 focus-visible:outline-indigo-600">Sources ({message.sources.length}) <span aria-hidden="true">{showSources ? '−' : '+'}</span></button>
      {showSources && <div className="mt-3 space-y-3">{message.sources.map((source, index) => <SourceCard key={source.citation_number || index} source={source} onHighlight={onCitation} />)}</div>}
    </div>}
  </div>
}
