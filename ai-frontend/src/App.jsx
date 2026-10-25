import { useState, useRef, useEffect } from 'react'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好，我是你的企业级 RAG 助手。' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  // 每次消息更新，自动滚动到最底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    
    const question = input
    const newMessages = [...messages, { role: 'user', content: question }]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    // 准备一个空的 AI 消息占位，用于流式追加文字
    setMessages([...newMessages, { role: 'assistant', content: '' }])

    try {
      // ★ 向云端服务器发起真实的流式请求
      const response = await fetch('http://124.220.164.171:8000/chat_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

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
              // 如果是文本，追加到界面
              if (data.text) {
                fullText += data.text
                setMessages(prev => {
                  const last = prev[prev.length - 1]
                  return [...prev.slice(0, -1), { ...last, content: fullText }]
                })
              }
              // 如果收到来源信息，可以打印看看
              if (data.type === 'sources') {
                console.log('引用来源:', data.sources)
              }
            } catch (e) {
              // 忽略解析不完整的 JSON 碎片
            }
          }
        }
      }
    } catch (error) {
      console.error('请求失败:', error)
      setMessages(prev => {
        const last = prev[prev.length - 1]
        return [...prev.slice(0, -1), { ...last, content: "请求超时或失败，请检查云端后端服务或跨域配置。" }]
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="bg-white shadow-sm p-4 text-center text-xl font-bold text-gray-700">
        🤖 商业级 AI 助手
      </header>
      
      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[70%] p-3 rounded-lg ${
              msg.role === 'user'
                ? 'bg-blue-500 text-white rounded-tr-none'
                : 'bg-white text-gray-800 shadow-sm rounded-tl-none'
            }`}>
              {msg.content || (isLoading && index === messages.length - 1 ? "正在思考..." : "")}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

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