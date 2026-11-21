import { useEffect, useRef, useState } from 'react'
import Layout from '../components/Layout.jsx'
import ChatInput from '../components/ChatInput.jsx'
import MessageBubble from '../components/MessageBubble.jsx'
import { askQuestion, searchChunks } from '../api/chat.js'

const EXAMPLES = ['What are the key qualifications?', 'Summarize the main responsibilities.', 'What dates or deadlines are mentioned?']

function friendlyError(error) {
  if (error.status === 502 || error.status === 503) return "The AI service is unavailable. Check the server's GROQ_API_KEY and model."
  return error.message || 'Something went wrong. Please try again.'
}

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [waiting, setWaiting] = useState(false)
  const [lastRequest, setLastRequest] = useState(null)
  const logRef = useRef(null)

  useEffect(() => { logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' }) }, [messages, waiting])

  async function send(request, retry = false) {
    setLastRequest(request)
    if (!retry) setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'user', text: request.question }])
    setWaiting(true)
    setMessages((current) => [...current.filter((message) => message.role !== 'error'), { id: 'typing', role: 'typing' }])
    try {
      if (request.searchOnly) {
        const result = await searchChunks({ query: request.question, top_k: request.top_k, document_id: request.document_id, mode: request.mode })
        setMessages((current) => [...current.filter((message) => message.role !== 'typing' && message.role !== 'error'), { id: crypto.randomUUID(), role: 'search', results: result.results || [] }])
      } else {
        const result = await askQuestion(request)
        setMessages((current) => [...current.filter((message) => message.role !== 'typing' && message.role !== 'error'), { id: crypto.randomUUID(), role: 'assistant', answer: result.answer, sources: result.sources || [] }])
      }
    } catch (error) {
      setMessages((current) => [...current.filter((message) => message.role !== 'typing'), { id: crypto.randomUUID(), role: 'error', text: friendlyError(error) }])
    } finally {
      setWaiting(false)
    }
  }

  function highlightSource(number) {
    const element = document.getElementById(`source-${number}`)
    element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (element) {
      element.classList.add('ring-2', 'ring-indigo-400')
      window.setTimeout(() => element.classList.remove('ring-2', 'ring-indigo-400'), 1800)
    }
  }

  const hasError = messages.some((message) => message.role === 'error')
  return <Layout>
    <main className="mx-auto flex h-[calc(100vh-73px)] max-w-5xl flex-col px-3 py-4 sm:px-6 sm:py-6">
      <div className="mb-4 shrink-0"><p className="text-sm font-semibold text-indigo-600">Ask your documents</p><h1 className="text-2xl font-bold tracking-tight text-slate-900">Chat</h1></div>
      <section ref={logRef} aria-label="Conversation" aria-live="polite" aria-relevant="additions text" className="min-h-0 flex-1 space-y-4 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-100/70 p-3 sm:p-5">
        {messages.length === 0 && <div className="flex min-h-full flex-col items-center justify-center py-8 text-center">
          <span className="grid size-12 place-items-center rounded-2xl bg-indigo-100 text-xl font-bold text-indigo-700" aria-hidden="true">D</span>
          <h2 className="mt-4 text-lg font-semibold text-slate-900">What would you like to know?</h2>
          <p className="mt-1 text-sm text-slate-500">Ask a question grounded in your uploaded files.</p>
          <div className="mt-5 flex max-w-2xl flex-wrap justify-center gap-2">{EXAMPLES.map((example) => <button key={example} type="button" onClick={() => send({ question: example, top_k: 4, mode: 'hybrid', searchOnly: false })} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 hover:border-indigo-300 hover:text-indigo-700 focus-visible:outline-2 focus-visible:outline-indigo-600">{example}</button>)}</div>
        </div>}
        {messages.map((message) => <MessageBubble key={message.id} message={message} onRetry={() => lastRequest && send(lastRequest, true)} onCitation={highlightSource} />)}
      </section>
      <div className="mt-3 shrink-0"><ChatInput onSend={send} waiting={waiting || hasError} /></div>
    </main>
  </Layout>
}
