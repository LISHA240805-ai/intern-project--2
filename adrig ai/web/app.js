const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? 'http://localhost:8000' : ''

const messagesEl = document.getElementById('messages')
const form = document.getElementById('form')
const input = document.getElementById('input')

function appendMessage(text, cls='bot'){
  const el = document.createElement('div')
  el.className = 'message ' + cls
  const b = document.createElement('div')
  b.className = 'bubble'
  b.textContent = text
  el.appendChild(b)
  messagesEl.appendChild(el)
  messagesEl.scrollTop = messagesEl.scrollHeight
}

async function callMCP(tool, inputObj){
  const res = await fetch(API_BASE + '/mcp/execute', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({tool_name: tool, input: inputObj})
  })
  if(!res.ok){
    const err = await res.text()
    return {error: err}
  }
  return await res.json()
}

form.addEventListener('submit', async (e)=>{
  e.preventDefault()
  const q = input.value.trim()
  if(!q) return
  appendMessage(q, 'user')
  input.value = ''

  appendMessage('Searching knowledge base...', 'bot')
  const search = await callMCP('qa_search', {query: q, limit: 5})
  if(search.error){ appendMessage('Search error: ' + JSON.stringify(search), 'bot'); return }

  let contextText = ''
  if(search.results && search.results.length>0){
    search.results.forEach(r=>{
      appendMessage('KB: ' + r.question + '\n' + r.answer, 'bot')
      contextText += r.answer + '\n'
    })
  } else {
    appendMessage('No KB matches found.', 'bot')
  }

  appendMessage('Generating answer...', 'bot')
  const prompt = `User question: ${q}\nCONTEXT: ${contextText}\nProvide a helpful answer.`
  const gen = await callMCP('llm_generate', {prompt})
  if(gen.error){ appendMessage('LLM error: ' + JSON.stringify(gen), 'bot'); return }
  appendMessage(gen.text || JSON.stringify(gen), 'bot')
})
