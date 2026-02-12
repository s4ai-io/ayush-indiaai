# PopCash Frontend - Next.js Intelligence UI

The PopCash frontend is a modern, mobile-first application built with **Next.js 16** and **React 19**. It utilizes the **App Router** for efficient navigation and server-side optimizations, providing a seamless interface for managing popCoins and interacting with AI agents via **CopilotKit**.

## 🏗️ Technology Stack

- **Framework**: Next.js 16 (App Router)
- **Core**: React 19 + TypeScript
- **AI Integration**: CopilotKit & LlamaIndex AI UI
- **Styling**: TailwindCSS 4 (Utility-first)
- **Icons**: Lucide React & React Icons
- **Charts**: Recharts

## 🚀 Setup & Installation

### 1. Prerequisites
- Node.js 18 or higher
- npm 9 or higher

### 2. Install Dependencies
Navigate to the `frontend` directory and install the required packages:

```bash
npm install
```

### 3. Start Development Server
```bash
npm run dev
```
The application will be available at: **http://localhost:3000** (Next.js default).

### 4. Build for Production
```bash
npm run build
npm start
```

## 📂 Project Structure

- `src/app/`: Next.js App Router (pages and layouts).
- `src/components/`: Modular UI components and tool renderers.
- `src/context/`: React context providers for global state.
- `src/styles/`: Global styles and Tailwind configuration.
- `public/`: Static assets and icons.

## 📱 Features

- **Dashboard**: Real-time balance tracking and transaction history.
- **AI Assistant**: Intelligent chat powered by CopilotKit for rewards optimization.
- **Analytics**: Deep-dive spending insights and goal tracking.
- **Mobile-First**: Responsive design optimized for small screens.
