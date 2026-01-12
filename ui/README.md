# Stock Analysis UI

A SvelteKit frontend for the Stock Analysis application. Browse Chinese A-share stocks, view detailed financial data with analysis scores, and chat with AI for insights.

## Features

- **Stock Browser**: Search and filter stocks by code, company name, classification, and industry
- **Stock Details**: Combined view with analysis scores, metrics, CNInfo data, and Yahoo Finance data
- **AI Chat** (Coming Soon): Ask questions about stocks and get AI-powered insights
- **Responsive Design**: Clean, modern UI optimized for all screen sizes
- **Real-time Updates**: Automatically queues data fetching for stocks with missing information

## Prerequisites

- Node.js 18+ and npm
- The FastAPI backend running on `http://localhost:8000`

## Getting Started

### Installation

```bash
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser. The app will hot-reload as you make changes.

### Type Checking

Run TypeScript and Svelte validation:

```bash
npm run check
```

Watch mode:

```bash
npm run check:watch
```

### Building

Create a production build:

```bash
npm run build
```

Preview the production build locally:

```bash
npm run preview
```

## Project Structure

```text
src/
├── app.css                     # Global styles
├── app.html                    # HTML template
├── routes/
│   ├── +page.svelte            # Home page
│   ├── +layout.svelte          # Main layout with navigation
│   ├── stocks/
│   │   ├── +page.svelte        # Stock list with search & filters
│   │   └── [code]/
│   │       └── +page.svelte    # Stock detail (analysis + data)
│   └── chat/
│       └── +page.svelte        # AI chat interface
└── lib/
    ├── api.ts                  # API client
    ├── types.ts                # TypeScript types
    └── index.ts                # Exports
```

## API Integration

The frontend communicates with the FastAPI backend via the `/api` endpoint, which is proxied to `http://localhost:8000` during development (configured in `vite.config.ts`).

### API Endpoints Used

- `GET /stocks` - List stocks with pagination and filtering
- `GET /stocks/{code}` - Get stock details with CNInfo and Yahoo Finance data
- `GET /analysis/{code}` - Get analysis scores and metrics for a stock

## Technologies

- **SvelteKit 2** - Framework
- **Svelte 5** - UI components
- **TypeScript** - Type safety
- **Vite** - Build tool

## License

See parent project LICENSE.
