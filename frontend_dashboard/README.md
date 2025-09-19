# ScrumBot Frontend Dashboard

AI-powered meeting assistant dashboard built with Next.js.

## 🚀 Quick Start

### Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

### Production Testing
```bash
# Test production build locally
npm run build
npm run start
```

## 🔧 Environment Setup

### Local Development
1. Copy environment template:
```bash
cp .env.example .env.local
```

2. Update `.env.local` with your local backend URL:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8080
```

### Production Deployment
1. Set environment variables in Vercel dashboard:
   - `NEXT_PUBLIC_API_URL`: Your production API URL
   - `NEXT_PUBLIC_WEBSOCKET_URL`: Your production WebSocket URL
   - `NEXT_PUBLIC_ENV`: `production`

## 📁 Project Structure

```
frontend_dashboard/
├── app/                    # Next.js App Router pages
│   ├── page.js            # Dashboard home
│   ├── meetings/          # Meeting history & details
│   ├── action_items/      # AI-generated tasks
│   ├── integrations/      # Platform connections
│   └── layout.js          # Root layout
├── components/            # Reusable UI components
├── lib/                   # Utilities & configuration
│   ├── config.js         # Environment configuration
│   └── api.js            # API client service
└── public/               # Static assets
```

## 🔗 API Integration

The dashboard connects to the ai_processing backend:

- **Health Check**: `/health`
- **Meetings**: `/get-meetings`
- **Tasks**: `/api/tasks`
- **Transcripts**: `/api/transcripts/{meetingId}`
- **Integrations**: `/api/integration-status`

## 🎯 Features

- **Real-time Dashboard**: Live backend health monitoring
- **Meeting Management**: View transcripts, summaries, action items
- **Task Management**: AI-generated tasks with approval workflow
- **Integration Status**: Platform connection management
- **Responsive Design**: Mobile-friendly interface

## 🚀 Deployment

### Vercel (Recommended)
1. Connect GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Manual Deployment
```bash
npm run build
npm run start
```

## 🔧 Development Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## 🌐 Environment Variables

| Variable | Description | Development | Production |
|----------|-------------|-------------|------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8080` | Your production API |
| `NEXT_PUBLIC_WEBSOCKET_URL` | WebSocket URL | `ws://localhost:8080` | Your production WS |
| `NEXT_PUBLIC_ENV` | Environment | `development` | `production` |