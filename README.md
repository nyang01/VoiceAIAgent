# Layla — Voice AI Personal Assistant

> **"Hi Layla, read my emails."** — She reads them.
> **"Reply to the first one saying I'll be there."** — She sends it.
> **"What's on my schedule tomorrow?"** — She tells you.
> **"What's the weather in London?"** — She looks it up and tells you.

Layla is a voice AI **agent**, not a chatbot. She doesn't tell you how to do things — she does them. Real emails sent. Real calendar events created. Real-time web answers. All through natural voice conversation.

Built for the [GDG London "Build with AI x IWD 2026" Hackathon](https://gdg-london-hackathon.vercel.app/).

---

## Features

### Email (Gmail)
- **Read** — "What are my latest emails?"
- **Search** — "Find emails from Sarah about the contract"
- **Send & reply** — "Reply saying I'll get back to them by Friday"
- **Read in full** — "Read me the full content of that email"
- **Archive** — "Archive that email"

### Calendar (Google Calendar)
- **View** — "What's on my schedule today?"
- **Create** — "Add a team meeting on Friday at 2pm"
- **Modify** — "Move it to 4pm" (preserves duration automatically)
- **Delete** — "Cancel that meeting"
- Supports multiple calendars — "Add it to my work calendar"

### Web Search (Google Search Grounding)
- **Weather** — "What's the weather in London?"
- **General knowledge** — "How long does it take to drive from London to Manchester?"
- **News** — "What's the latest AI news?"
- Powered by Gemini with Google Search grounding for real-time data

### Memory & Context
- **Long-term memory** — remembers your email contacts, preferences, and facts forever across sessions
  - "Remember that I prefer morning meetings" — recalled in every future session
  - "Forget my coffee preference" — removed from memory
  - Contacts auto-learned from your email senders
- **Session memory** — retains conversation context for 2 hours, so you can ask follow-up questions naturally
  - Smart compaction: after 20 messages, older messages are summarized to preserve context while keeping token costs low
- **Session-aware greeting** — reports new emails since your last session

## Accessibility

Layla is fully voice-driven — no screen interaction required. This makes it especially impactful for visually impaired users, providing a natural spoken interface to email, calendar, and the web.

---

## How It Works

```
iPhone                               Server (Python)
┌──────────────────┐                ┌──────────────────────────────────┐
│                  │     HTTPS      │  FastAPI /api/chat                │
│  "Hi Layla"      │  ──────────>   │    │                              │
│   (Vocal         │                │    ├─ Greeting? ─> Fast Path     │
│    Shortcut)     │                │    │   (zero LLM tokens, <1s)     │
│                  │                │    │                              │
│  iOS Shortcuts:  │                │    └─ Everything else ──>         │
│  1. Dictate      │                │       Gemini 2.5 Flash Lite      │
│  2. POST to API  │  <──────────   │         ├─ Gmail tools (5)       │
│  3. Speak reply  │     JSON       │         ├─ Calendar tools (5)    │
│                  │                │         ├─ Web Search             │
└──────────────────┘                │         └─ Memory tools (2)      │
                                    └──────────────────────────────────┘
                                     13 tools | 2-hour sessions
```

Currently built for **iPhone** using iOS Shortcuts for voice input (STT) and spoken output (TTS). **Gemini** handles all intelligence on the server. No app needed — just an iOS Shortcut.

---

## Key Technical Design

- **Two-model architecture** — Gemini 2.5 Flash Lite for the main agent. Gemini 2.5 Flash with Google Search grounding for real-time web queries.
- **Fast greeting path** — Greetings bypass the LLM entirely. Python queries Gmail and Calendar APIs directly. Sub-second response, zero token cost.
- **Batch API for emails** — All emails fetched in parallel using Google's batch request API for faster responses.
- **Session-aware greeting** — Tracks when each session ends. Next greeting reports only what's new since then. Counts only Primary inbox, filtering out Promotions/Social/Updates.
- **History compaction** — After 20 messages, older messages are summarized into a concise context block, preserving key details (IDs, names, actions) while keeping token costs low.
- **Parallel tool execution** — Gemini can call multiple tools at once (e.g., read_emails + read_calendar). All results returned in a single response.

---

## Quick Start (Demo)

### 1. Clone and install

```bash
git clone https://github.com/nicnacnic/VoiceAIAgent.git
cd VoiceAIAgent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Google Cloud OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Gmail API** and **Google Calendar API**
3. Configure OAuth consent screen (External, add your email as test user)
4. Add scopes: `gmail.modify` and `calendar`
5. Create OAuth credentials (Desktop app type) → download as `credentials.json`
6. Generate token:

```bash
python generate_token.py
```

This opens a browser for Google sign-in and creates `token.json`.

### 4. Start the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Expose with ngrok

```bash
ngrok http 8000
```

### 6. iOS Shortcut

Create a shortcut named **"Layla"** with these actions in a Repeat loop:

1. **Dictate Text** (stop after pause)
2. **URL** → `https://YOUR_NGROK_URL/api/chat` (copy the Forwarding URL from ngrok)
3. **Get Contents of URL** → POST, Headers: `Content-Type: application/json` + `ngrok-skip-browser-warning: true`, Body: `{"message": Dictated Text, "user_id": "your-name"}`
4. **Get Dictionary Value** → key: `reply`
5. **Speak Text** → Dictionary Value
6. **Get Dictionary Value** → key: `action`
7. **If** action **is** `stop` → **Exit Shortcut**

Activate hands-free: **Settings > Accessibility > Vocal Shortcuts** → add **"Hi Layla"**.

---

## Project Structure

```
├── main.py               # FastAPI server with /api/chat endpoint
├── agent.py              # Gemini agent — 13 tools, function calling loop
├── session.py            # Session manager — 2-hour TTL, expiry tracking
├── memory.py             # Long-term memory — contacts, facts, preferences
├── auth.py               # Google OAuth2 credential management
├── tools/
│   ├── gmail_tools.py    # read, search, send, archive, get_full_email
│   └── calendar_tools.py # read, create, modify, delete, list_calendars
├── generate_token.py     # One-time OAuth token generator
├── requirements.txt
├── Procfile              # Cloud deployment (Railway/Render)
└── .env.example
```

## Tech Stack

- **LLM**: Gemini 2.5 Flash Lite (agent) + Gemini 2.5 Flash (web search)
- **Backend**: FastAPI + Uvicorn
- **APIs**: Google Gmail, Google Calendar, Google Search
- **Auth**: OAuth2 (google-auth-oauthlib)
- **Voice**: iOS Shortcuts (STT + TTS)
- **Tunnel**: ngrok

## Future Considerations

- **Cost at scale** — Gemini 2.5 Flash Lite: $0.10/1M input, $0.40/1M output tokens. Gemini 2.5 Flash (web search): $0.30/1M input, $2.50/1M output tokens. Google Search grounding: $35/1,000 grounded prompts beyond 1,500/day free allowance. Gmail and Calendar APIs are free. Estimated ~$0.50–1.50/month per user depending on usage.
- **Multi-user distribution** — hosted SaaS with Google OAuth onboarding, so users connect their own Google account without any technical setup.
- **Extensible tools** — any API can be added as a new tool (e.g., Google Maps, YouTube, Spotify). Add a tool file, register it, and the agent loop handles the rest.

## License

MIT
