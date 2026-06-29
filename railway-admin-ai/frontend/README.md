# 🎨 RailVera Frontend

Next.js 14 web application for the RailVera Decision Support AI Portal.

---

## Overview

This is the user-facing web interface that allows:
- **Employees** to submit cases, upload documents, and ask eligibility questions
- **Personnel Officers** to review AI decisions and approve or reject cases
- **Everyone** to generate official PDF decision reports

Built with **Next.js 14**, **TypeScript**, and **Tailwind CSS**.

---

## Requirements

- **Node.js 18 or higher** — [Download here](https://nodejs.org/)
- **npm** (comes with Node.js)
- The **backend server** must be running on port 8000

---

## Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure the API URL

Create a `.env.local` file in the `frontend/` folder:

```bash
# Windows
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local

# macOS/Linux
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 3. Start the development server

```bash
npm run dev
```

Open **http://localhost:3000** in your browser. ✅

---

## Available Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Start development server with hot-reloading |
| `npm run build` | Build the production bundle |
| `npm run start` | Serve the production build |
| `npm run lint` | Check code for issues |

---

## Project Structure

```
frontend/
├── app/                         # Next.js App Router pages
│   ├── layout.tsx               # Root layout (fonts, global styles)
│   ├── page.tsx                 # Login / landing page
│   └── chat/
│       └── page.tsx             # Main application (cases, chat, upload)
│
├── components/
│   └── chat/
│       └── MessageBubble.tsx    # Chat message with markdown renderer
│
├── lib/
│   └── api.ts                   # All HTTP calls to the backend
│
├── public/                      # Static assets
├── .env.local                   # 🔒 Your API URL (create this yourself)
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

---

## How the UI Works

### Login Page (`/`)
- User enters their Employee ID and password
- On success, a JWT token is stored in `localStorage`
- Redirects to the chat application

### Chat Page (`/chat`)
The main interface is split into three panels:

**Left Sidebar**
- Domain selector (Promotion, Transfer, Medical, etc.)
- Case history — load previous cases
- Document upload area
- Document checklist showing which required files have been submitted

**Centre Panel (Chat)**
- Conversation thread with the AI Personnel Officer
- Messages render markdown properly (bold, lists, headings)
- Applied rule citations shown below each AI response

**Right Sidebar** *(Personnel Officers only)*
- Current case status
- Approve / Reject buttons
- Generate PDF Report button

---

## Connecting to a Different Backend

If your backend runs on a different port or host, update `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://your-server-address:8000
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Blank page on `/chat` | Make sure backend is running on port 8000 |
| `401 Unauthorized` errors | Your session expired — log out and log back in |
| Documents show "Verified" instantly | OCR runs in simulation mode (Tesseract not installed on backend) |
| Chat has no response | Check that the backend Gemini key is configured correctly |
