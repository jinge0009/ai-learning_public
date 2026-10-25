import { useState } from 'react'

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '你好，我是你的 AI 助手。' }
  ])
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return
    const newMessages = [...messages, { role: 'user', content: input }]
    setMessages(newMessages)
    setInput('')

    setTimeout(() => {
      setMessages([
        ...newMessages,
        { role: 'assistant', content: '这是一个模拟的回答，明天我就会接入真正的 RAG 后端了！' }
      ])
    }, 1000)
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
              {msg.content}
            </div>
          </div>
        ))}
      </main>
      <footer className="bg-white p-4 shadow-md">
        <div className="max-w-4xl mx-auto flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="请输入你的问题..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            发送
          </button>
        </div>
      </footer>
    </div>
  )
}

export default App