# Optimised Math Learning - Next.js Frontend

This is the Next.js frontend for the Optimised Math Learning application, migrated from a Vite-React setup to a modular Next.js application with App Router, TypeScript, and Tailwind CSS v4.

## Tech Stack

- **Next.js 16** with App Router
- **TypeScript** for type safety
- **Tailwind CSS v4** for styling
- **shadcn/ui** for UI components
- **react-katex** for math rendering
- **axios** for API communication

## Project Structure

```
next-frontend/
├── app/
│   ├── layout.tsx          # Root layout with KaTeX CSS imports
│   ├── page.tsx            # Landing page (redirect to arena)
│   └── arena/
│       └── page.tsx        # Game arena page
├── components/
│   ├── arena/              # Game-specific components
│   │   ├── XPBar.tsx
│   │   ├── ProblemDisplay.tsx
│   │   ├── AnswerInput.tsx
│   │   ├── FeedbackCard.tsx
│   │   └── GameArena.tsx   # Main game container
│   └── ui/                 # shadcn/ui components
├── lib/
│   ├── api.ts              # Axios client with env config
│   ├── types.ts            # TypeScript types for API responses
│   └── utils.ts            # Utility functions
└── .env.local              # Environment variables
```

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Python backend running on port 8000 (see parent directory)

### Installation

```bash
npm install
```

### Environment Configuration

Create a `.env.local` file in the root directory:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Running the Development Server

1. Start the Python backend (from parent directory):
```bash
source .venv/bin/activate
python main.py
```

2. Start the Next.js development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Architecture

### Backend Integration

The frontend is a thin client that communicates with the Python FastAPI backend via REST API. The backend remains the "Single Source of Truth" for:
- Session state management
- Math problem generation
- Database persistence
- Scoring logic

### Component Design

The application follows a modular component architecture:
- **XPBar**: Displays XP, streak, and flawless bonus status
- **ProblemDisplay**: Renders math problems using KaTeX
- **AnswerInput**: Handles user input for answers
- **FeedbackCard**: Shows feedback after answer submission
- **GameArena**: Main container orchestrating the game loop

### Game Flow

1. Landing page redirects to `/arena`
2. GameArena initializes by fetching curriculum and starting a session
3. Problems are fetched from the backend based on current state
4. User submits answers via AnswerInput
5. Backend evaluates answers and returns updated state
6. Feedback is displayed and next problem is loaded

## Current Status

✅ **Completed:**
- Next.js project setup with TypeScript and Tailwind CSS v4
- shadcn/ui integration with core components
- API client with typed functions
- Modular component architecture
- Landing page and arena routing
- KaTeX integration for math rendering
- Environment variable configuration

⚠️ **Known Issue:**
The backend session storage uses in-memory storage (`ACTIVE_SESSIONS` dictionary) which may cause session loss if the backend is restarted. The frontend is correctly implemented, but the full game loop requires the backend to maintain session state properly.

## Migration Notes

This frontend was migrated from a flat Vite-React setup to:
- Improve code organization with modular components
- Enable better type safety with TypeScript
- Provide a more scalable architecture for future features
- Leverage Next.js App Router for better routing and performance

The old `frontend/` directory (Vite-React) is preserved as a reference until this migration is fully verified.
