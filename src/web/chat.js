const form = document.getElementById('chat-form');
const input = document.getElementById('question');
const sendButton = document.getElementById('send-button');
const newChatButton = document.getElementById('new-chat');
const conversation = document.getElementById('conversation');
const messages = document.getElementById('messages');
const welcome = document.getElementById('welcome');
let busy = false;
let history = [];
const labels = {
  answered: 'Answered', clarification_needed: 'More detail needed',
  insufficient_evidence: 'Insufficient evidence'
};
const footnote = document.querySelector('.footnote');
if (footnote) footnote.textContent = 'Uses up to 8 previous messages. New chat or refresh clears memory. Model checks can make mistakes.';
function scrollToLatest() { conversation.scrollTop = conversation.scrollHeight; }
function resizeInput() {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 150) + 'px';
}
function setBusy(value) {
  busy = value;
  sendButton.disabled = input.disabled = newChatButton.disabled = value;
  sendButton.textContent = value ? 'Waiting…' : 'Send';
}
function createMessage(role) {
  const article = document.createElement('article');
  article.className = `message ${role}`;
  const speaker = document.createElement('div');
  speaker.className = 'speaker';
  speaker.textContent = role === 'user' ? 'You' : 'SupportLens';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  article.append(speaker, bubble);
  messages.appendChild(article);
  return { article, bubble };
}
function appendText(parent, text, className) {
  const p = document.createElement('p');
  p.className = className;
  p.textContent = text;
  parent.appendChild(p);
}
function renderMessage(message, kind, label, text, note = '') {
  message.bubble.replaceChildren();
  const badge = document.createElement('span');
  badge.className = 'badge'; badge.dataset.kind = kind; badge.textContent = label;
  message.bubble.appendChild(badge);
  appendText(message.bubble, text, 'message-text');
  if (note) appendText(message.bubble, note, 'verification');
}
function addTypingIndicator() {
  const message = createMessage('assistant');
  const dots = document.createElement('div'); dots.className = 'typing';
  dots.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < 3; i++) dots.appendChild(document.createElement('span'));
  message.bubble.appendChild(dots);
  appendText(message.bubble, 'Reading context, retrieving evidence and checking the response…', 'typing-label');
  return message;
}
function addSources(bubble, sources) {
  if (!Array.isArray(sources) || !sources.length) return;
  const details = document.createElement('details');
  const summary = document.createElement('summary');
  summary.textContent = `Sources (${sources.length})`;
  const list = document.createElement('ul'); list.className = 'sources';
  for (const source of sources) {
    const item = document.createElement('li');
    const title = document.createElement('strong');
    title.textContent = `[${source.id}] ${source.title}`;
    const location = document.createElement('span');
    location.className = 'source-location'; location.textContent = source.source;
    item.append(title, location); list.appendChild(item);
  }
  details.append(summary, list); bubble.appendChild(details);
}
function renderResponse(message, data) {
  if (data?.withheld === true) {
    renderMessage(message, 'withheld', 'Answer withheld',
      'I could not confirm that the draft was supported by the evidence.',
      'The draft has not been displayed or added to memory.');
    return null;
  }
  if (data?.withheld !== false || !data.answer ||
      typeof data.answer.answer !== 'string' || !Object.hasOwn(labels, data.answer.status)) {
    throw new Error('The server returned an unexpected response format.');
  }
  const answer = data.answer;
  if (answer.status === 'answered' && data.verification_status !== 'supported') {
    renderMessage(message, 'withheld', 'Answer withheld',
      'This response did not include a successful claim-support check.');
    return null;
  }
  renderMessage(message, answer.status, labels[answer.status], answer.answer,
    answer.status === 'answered'
      ? 'Model-based support check passed. This check can still make mistakes.'
      : 'Claim-support verification was skipped for this non-answer response.');
  addSources(message.bubble, data.sources);
  return answer.answer;
}
function errorMessage(data, status) {
  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.map(x => x.msg || 'Invalid request.').join(' ');
  return `The request failed (HTTP ${status}).`;
}
async function sendQuestion(question) {
  if (busy) return;
  welcome.hidden = true; setBusy(true);
  appendText(createMessage('user').bubble, question, 'message-text');
  input.value = ''; resizeInput();
  const reply = addTypingIndicator(); scrollToLatest();
  const controller = new AbortController();
  // Context resolution, generation and verification can each take up to 60s.
  const timeout = setTimeout(() => controller.abort(), 210000);
  try {
    const response = await fetch('/ask', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history }), signal: controller.signal
    });
    let data;
    try { data = await response.json(); }
    catch (error) {
      if (error.name === 'AbortError') throw error;
      throw new Error(`Unreadable server response (HTTP ${response.status}).`);
    }
    if (!response.ok) throw new Error(errorMessage(data, response.status));
    const displayedAnswer = renderResponse(reply, data);
    if (displayedAnswer !== null) {
      // Keep only successful exchanges. Omit an oversized exchange rather
      // than truncate it and potentially change its meaning.
      if (displayedAnswer.length <= 4000) {
        history.push({ role: 'user', content: question },
                     { role: 'assistant', content: displayedAnswer });
        history = history.slice(-8);
      } else {
        history = [];
        appendText(reply.bubble, 'Memory cleared because this response exceeds the context limit.', 'verification');
      }
    }
  } catch (error) {
    const text = error.name === 'AbortError'
      ? 'The browser stopped waiting after 210 seconds. The server may still be processing this question.'
      : error instanceof TypeError
        ? 'Could not reach SupportLens. Check that your local server is running.'
        : error.message || 'An unexpected error occurred.';
    renderMessage(reply, 'error', 'Request unsuccessful', text,
      'This exchange was not added to memory.');
  } finally {
    clearTimeout(timeout); setBusy(false); scrollToLatest(); input.focus();
  }
}
form.addEventListener('submit', event => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) {
    input.setCustomValidity('Please enter a question.'); input.reportValidity(); return;
  }
  input.setCustomValidity(''); sendQuestion(question);
});
input.addEventListener('input', () => { input.setCustomValidity(''); resizeInput(); });
input.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault(); if (!busy) form.requestSubmit();
  }
});
document.querySelectorAll('.suggestion').forEach(button => {
  button.addEventListener('click', () => {
    if (busy) return;
    input.value = button.textContent.trim(); input.setCustomValidity(''); form.requestSubmit();
  });
});
newChatButton.addEventListener('click', () => {
  if (busy) return;
  history = []; messages.replaceChildren(); welcome.hidden = false;
  input.value = ''; input.setCustomValidity(''); resizeInput(); input.focus();
});
