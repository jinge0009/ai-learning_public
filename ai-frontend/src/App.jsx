import { useState, useRef, useEffect } from 'react'
import Markdown from 'react-markdown'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好，我是你的企业级 RAG 助手。' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  
  // ★ 新增：侧边栏控制
  const [showSidebar, setShowSidebar] = useState(false)
  const [documents, setDocuments] = useState([])
  
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 获取文档列表
  const fetchDocuments = async () => {
    try {
      const response = await fetch('/api/documents')
      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents || [])
      }
    } catch (e) { console.error("获取文档失败", e) }
  }

  // 删除文档
  const handleDeleteDoc = async (name) => {
    if (!window.confirm(`确定要删除 ${name} 吗？`)) return
    try {
      const response = await fetch(`/api/documents/${name}`, { method: 'DELETE' })
      if (response.ok) {
        fetchDocuments()
        alert("删除成功")
      }
    } catch (e) { console.error(e) }
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    
    const question = input
    const newMessages = [...messages, { role: 'user', content: question }]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    // 准备空气泡占位，并带上 sources 字段
    setMessages([...newMessages, { role: 'assistant', content: '', sources: [] }])

    const history = messages.slice(-5).map(msg => ({ role: msg.role, content: msg.content }))

    try {
      const response = await fetch('/api/chat_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let fullText = ''
      let currentSources = []

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.text) {
                fullText += data.text
                setMessages(prev => {
                  const last = prev[prev.length - 1]
                  return [...prev.slice(0, -1), { ...last, content: fullText }]
                })
              }
              // ★ 收到来源数据
              if (data.type === 'sources') {
                currentSources = data.sources
                setMessages(prev => {
                  const last = prev[prev.length - 1]
                  return [...prev.slice(0, -1), { ...last, sources: currentSources }]
                })
              }
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      console.error('请求失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden relative">
      
      {/* 侧边栏：文档管理 */}
      <div className={`fixed inset-y-0 left-0 w-64 max-w-[80vw] bg-white shadow-xl transform transition-transform duration-300 z-50 ${showSidebar ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-4 flex justify-between items-center border-b">
          <h2 className="font-bold text-gray-700">文档管理</h2>
          <button onClick={() => setShowSidebar(false)} className="text-gray-500 hover:text-red-500 font-bold">✕</button>
        </div>
        <div className="p-4 overflow-y-auto h-full pb-20">
          {documents.length === 0 ? <p className="text-sm text-gray-400">暂无文档</p> : (
            <ul className="space-y-2">
              {documents.map((doc, i) => (
                <li key={i} className="flex justify-between items-center bg-gray-50 p-2 rounded text-sm text-gray-700">
                  <span className="truncate max-w-[150px]" title={doc}>{doc}</span>
                  <button onClick={() => handleDeleteDoc(doc)} className="text-red-400 hover:text-red-600">删除</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* 遮罩层 */}
      {showSidebar && <div onClick={() => setShowSidebar(false)} className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"></div>}

      {/* 主聊天区 */}
      <div className="flex flex-col flex-1 h-full">
        <header className="bg-white shadow-sm p-4 flex justify-between items-center">
          <button onClick={() => {setShowSidebar(true); fetchDocuments();}} className="text-gray-600 hover:text-blue-500 font-bold text-sm px-4 py-2 border rounded-lg">
            📁 文档管理
          </button>
          <h1 className="text-xl font-bold text-gray-700">🤖 商业级 AI 助手</h1>
          <div className="w-24 flex justify-end">
            <input type="file" accept=".pdf,.txt,.docx" onChange={async (e) => {
              const file = e.target.files[0]; if(!file) return;
              setIsUploading(true); const fd = new FormData(); fd.append('file', file);
              await fetch('/api/upload', { method: 'POST', body: fd });
              setIsUploading(false); e.target.value = null; alert("上传成功");
            }} className="hidden" id="file-upload" />
            <label htmlFor="file-upload" className={`cursor-pointer px-4 py-2 rounded-lg text-white text-sm ${isUploading ? 'bg-gray-400' : 'bg-green-500 hover:bg-green-600'}`}>
              {isUploading ? '上传中' : '上传'}
            </label>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, index) => (
            <div key={index} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`max-w-[70%] p-3 rounded-lg ${
                msg.role === 'user' ? 'bg-blue-500 text-white rounded-tr-none' : 'bg-white text-gray-800 shadow-sm rounded-tl-none'
              }`}>
                <div className="prose prose-sm max-w-none">
                  {msg.content ? <Markdown>{msg.content}</Markdown> : (
                    isLoading && index === messages.length - 1 && (
                      <div className="flex space-x-1 items-center h-6">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    )
                  )}
                </div>
              </div>
              
              {/* ★ 渲染 AI 来源按钮 */}
              {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 ml-2">
                  <details className="text-sm text-gray-500 cursor-pointer">
                    <summary className="hover:text-blue-500">📚 查看引用 ({msg.sources.length})</summary>
                    <div className="mt-2 space-y-2 bg-gray-100 p-3 rounded-lg max-w-2xl">
                      {msg.sources.map((src, i) => (
                        <div key={i} className="border-l-2 border-blue-400 pl-2">
                          <p className="font-bold text-gray-700">{src.source} (相关度 {src.rerank_score})</p>
                          <p className="text-gray-600 text-xs mt-1">{src.content}...</p>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </main>

        <footer className="bg-white p-4 shadow-md">
          <div className="max-w-4xl mx-auto flex gap-2">
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSend()} placeholder="请输入你的问题..." disabled={isLoading} className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <button onClick={handleSend} disabled={isLoading} className={`px-6 py-2 rounded-lg text-white ${isLoading ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'}`}>
              {isLoading ? '思考中...' : '发送'}
            </button>
          </div>
        </footer>
      </div>
    </div>
  )
}
export default App