# ⚖️ Caselaw Viewer

A powerful desktop application for legal professionals to search, analyze, and interact with court case databases using AI.
- Note, please contact me directly at bbc@chintellalaw.com for the database of cases itself necessary for this program to work.

---

## ✨ Features

**Smart Search** — Find cases instantly with exact matching and intelligent fuzzy search that catches near-matches when exact results are sparse.

**AI-Powered Case Briefs** — Generate comprehensive case summaries with a single click. Choose from general briefs or topic-focused analysis on specific legal issues like custody modifications, attorney fees, jurisdiction, and dozens more.

**Interactive Case Chat** — Have a conversation with AI about any case. Ask follow-up questions, explore reasoning, and dig deeper into holdings and implications.

**Flexible Date Filtering** — Narrow results by date range with smart handling of partial dates (year-only or month-only records).

**Multiple Export Formats** — Save briefs as PDF, Word documents, or plain text. Copy prompts to clipboard for use in other tools.

**Customizable Brief Types** — Create your own brief templates focused on the legal topics you encounter most, organized into categories for quick access.

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/caselaw-viewer.git
cd caselaw-viewer

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

---

## 📖 Quick Start

1. **Configure your API key** — Go to *File → Settings* and enter your OpenAI API key (or use a local LMStudio model).

2. **Search for cases** — Type in the search bar and select which column to search. Toggle "Show Fuzzy Results" for broader matches.

3. **Generate a brief** — Right-click any case and select "Get Case Brief" or choose a topic-specific brief from the menu.

4. **Chat with a case** — Right-click and select "Chat About This Case" to start an interactive Q&A session.

5. **Manage brief types** — Go to *File → Manage Brief Types* to create custom templates for your practice areas.

---

## 🎨 Interface

The application features a clean dark theme optimized for extended reading sessions, with streaming AI responses that appear in real-time as they're generated.

---

## 📁 Project Structure

```
caselaw-viewer/
├── config/          # Settings, tooltips, and brief type definitions
├── core/            # Search engine, brief registry, HTML parsing
├── data/            # Data loading and chat storage
├── gui/             # Main window, dialogs, and widgets
├── services/        # Case, chat, and search orchestration
└── utils/           # Date filtering, file helpers, tooltips
```

---

## 📄 License

MIT License — See LICENSE file for details.
