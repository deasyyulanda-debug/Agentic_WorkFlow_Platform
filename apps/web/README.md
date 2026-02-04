# Agentic Workflow Platform - Frontend

Modern Next.js 14 frontend for the Agentic Workflow Platform, providing a beautiful and intuitive interface for managing AI workflows.

## 🎨 Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5.3+
- **Styling**: Tailwind CSS with custom design tokens
- **UI Components**: shadcn/ui inspired components
- **Data Fetching**: TanStack Query (React Query)
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Forms**: React Hook Form + Zod
- **Notifications**: Sonner

## 📁 Project Structure

```
apps/web/
├── app/                    # Next.js App Router pages
│   ├── dashboard/         # Dashboard page
│   ├── workflows/         # Workflows pages (list, create, detail)
│   ├── runs/              # Runs pages (list, detail)
│   ├── settings/          # Settings page
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Landing page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── layout/           # Layout components (Header, Footer)
│   ├── ui/               # UI primitives (Button, Card, etc.)
│   └── providers.tsx     # React Query provider
├── lib/                  # Utilities and API client
│   ├── api/             # API service modules
│   │   ├── client.ts    # Axios instance
│   │   ├── settings.ts  # Settings API
│   │   ├── workflows.ts # Workflows API
│   │   ├── runs.ts      # Runs API
│   │   └── artifacts.ts # Artifacts API
│   └── utils.ts         # Utility functions
├── types/               # TypeScript type definitions
│   └── api.ts          # API response types
└── package.json        # Dependencies
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

1. Install dependencies:

```bash
cd apps/web
npm install
```

2. Configure environment variables:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` if needed:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

3. Start development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm start
```

## 🎯 Features

### Dashboard
- Real-time stats (Active Providers, Workflows, Runs, Success Rate)
- Recent runs with status badges
- Active workflows overview
- Quick navigation to all features

### Workflows
- **List View**: Grid/list of all workflows with search and filters
- **Create**: Multi-step form builder with provider selection
- **Detail**: View workflow configuration and execution history
- **Validation**: Real-time workflow validation
- **Execution Modes**: Sequential, Parallel, Conditional

### Runs
- **Execute**: Start workflow runs with custom parameters
- **Monitor**: Real-time status updates (polling every 5 seconds)
- **History**: Complete run history with filters
- **Details**: View execution results, artifacts, and timing

### Settings
- **Provider Management**: Add/remove AI provider configurations
- **API Keys**: Secure storage and management
- **Testing**: Test provider connections
- **Activation**: Enable/disable providers

## 🎨 Design System

### Color Scheme
The application supports light and dark modes with CSS custom properties:

- **Primary**: Blue (#2563eb)
- **Secondary**: Purple
- **Success**: Green
- **Warning**: Yellow
- **Error**: Red
- **Muted**: Gray

### Components
All UI components follow the shadcn/ui design principles:

- **Button**: Multiple variants (default, outline, ghost, destructive)
- **Card**: Container with header, content, footer
- **Badge**: Status indicators with color variants
- **Input/Textarea**: Form inputs with validation
- **Label**: Form labels

## 📡 API Integration

### API Client
The `lib/api/client.ts` provides a configured Axios instance with:

- **Base URL**: Configured via `NEXT_PUBLIC_API_URL`
- **Request Interceptor**: Prepares for future auth token injection
- **Response Interceptor**: Global error handling
- **Timeout**: 30 seconds

### API Services
Each domain has a dedicated service module:

```typescript
// Example: Using the workflows API
import { workflowsApi } from "@/lib/api/workflows";

// List workflows
const workflows = await workflowsApi.list({ search: "test" });

// Create workflow
const workflow = await workflowsApi.create({
  name: "My Workflow",
  mode: "sequential",
  steps: [...]
});
```

### React Query Integration
Data fetching uses TanStack Query for:

- **Caching**: Automatic response caching
- **Refetching**: Background updates
- **Optimistic Updates**: Instant UI updates
- **Error Handling**: Centralized error management

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ["workflows"],
  queryFn: () => workflowsApi.list({}),
});
```

## 🔧 Configuration Files

### tsconfig.json
- Strict TypeScript with path aliases (`@/*`)
- ES2017 target for modern browsers

### tailwind.config.js
- Custom color palette with CSS variables
- Container utilities
- Custom animations

### next.config.js
- Optimized build configuration
- Environment variable handling

## 🧪 Development Tips

### Hot Reload
The dev server supports hot module replacement. Changes to components, styles, and pages are instantly reflected.

### Type Safety
All API responses are typed. Use the types from `types/api.ts`:

```typescript
import type { Workflow, Run, Settings } from "@/types/api";
```

### Utilities
Common utilities in `lib/utils.ts`:

```typescript
import { cn, formatDate, getStatusColor } from "@/lib/utils";
```

## 📝 API Endpoints Used

The frontend communicates with these backend endpoints:

- **Settings**: `/api/v1/settings/*` (9 endpoints)
- **Workflows**: `/api/v1/workflows/*` (8 endpoints)
- **Runs**: `/api/v1/runs/*` (8 endpoints)
- **Artifacts**: `/api/v1/artifacts/*` (6 endpoints)

See `API_DOCUMENTATION.md` in the root for full API details.

## 🚦 Status Indicators

Runs display real-time status with color-coded badges:

- **Queued**: Gray
- **Validating**: Blue
- **Running**: Yellow (auto-refreshes)
- **Completed**: Green
- **Failed**: Red
- **Cancelled**: Gray

## 🎭 Future Enhancements

- [ ] Dark mode toggle
- [ ] Real-time WebSocket updates
- [ ] Workflow visual designer (drag-and-drop)
- [ ] Advanced analytics dashboard
- [ ] Artifact preview/download
- [ ] User authentication
- [ ] Team collaboration features
- [ ] Workflow templates library

## 📄 License

Part of the Agentic Workflow Platform. See root LICENSE file.

## 🤝 Contributing

See root CONTRIBUTING.md for guidelines.

---

Built with ❤️ using Next.js and FastAPI
