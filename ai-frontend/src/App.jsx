import { useState, useRef, useEffect } from 'react'
import Markdown from 'react-markdown'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好，我是你的企业级 RAG 助手。' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const messagesEndRef = useRef(null)

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    
    const question = input
    const newMessages = [...messages, { role: 'user', content: question }]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    setMessages([...newMessages, { role: 'assistant', content: '' }])

    try {
      const response = await fetch('/api/chat_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
      })

      if (!response.ok) throw new Error('Network response was not ok')

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let fullText = ''

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
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      console.error('请求失败:', error)
      setMessages(prev => {
        const last = prev[prev.length - 1]
        return [...prev.slice(0, -1), { ...last, content: "请求失败，请检查云端服务。" }]
      })
    } finally {
      setIsLoading(false)
    }
  }

  // 上传文件
  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        const data = await response.json()
        alert(`上传成功！文件切分了 ${data.chunks} 块。`)
      } else {
        alert('上传失败，请检查文件格式或后端服务。')
      }
    } catch (error) {
      console.error('上传出错:', error)
      alert('上传网络错误！')
    } finally {
      setIsUploading(false)
      e.target.value = null // 允许重复上传同一个文件
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 顶部栏 */}
      <header className="bg-white shadow-sm p-4 flex justify-between items-center">
        <div className="w-24"></div>
        <h1 className="text-xl font-bold text-gray-700">🤖 商业级 AI 助手</h1>
        <div className="w-24 flex justify-end">
          <input 
            type="file" 
            accept=".pdf,.txt,.docx" 
            onChange={handleFileUpload} 
            className="hidden" 
            id="file-upload" 
          />
          <label 
            htmlFor="file-upload" 
            className={`cursor-pointer px-4 py-2 rounded-lg text-white text-sm transition-colors ${
              isUploading ? 'bg-gray-400' : 'bg-green-500 hover:bg-green-600'
            }`}
          >
            {isUploading ? '上传中' : '上传文档'}
          </label>
        </div>
      </header>
      
      {/* 聊天区 */}
      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[70%] p-3 rounded-lg ${
              msg.role === 'user'
                ? 'bg-blue-500 text-white rounded-tr-none'
                : 'bg-white text-gray-800 shadow-sm rounded-tl-none'
            }`}>
              <div className="prose prose-sm max-w-none">
                <Markdown>{msg.content}</Markdown>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

      {/* 底部输入区 */}
      <footer className="bg-white p-4 shadow-md">
        <div className="max-w-4xl mx-auto flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="请输入你的问题..."
            disabled={isLoading}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={isLoading}
            className={`px-6 py-2 rounded-lg text-white transition-colors ${
              isLoading ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'
            }`}
          >
            {isLoading ? '思考中...' : '发送'}
          </button>
        </div>
      </footer>
    </div>
  )
}

export default App