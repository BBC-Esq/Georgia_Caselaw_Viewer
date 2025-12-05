# Core Modules

- **search.py** — Implements a search engine with exact and fuzzy matching (using thefuzz) against DataFrame columns, with result caching for performance.
- **brief_registry.py** — Singleton registry that manages brief type definitions, handling loading/saving from YAML and providing category-based organization.
- **brief_utils.py** — Utility functions for building prompts, generating unique filenames, and resolving output paths for case briefs.
- **chat_models.py** — Data classes representing chat messages and case conversations, with serialization for persistence and OpenAI API formatting.
- **html_parser.py** — Extracts clean text content from HTML case files using BeautifulSoup, stripping scripts and styles.
- **initial_briefs.yaml** — Default brief type definitions shipped with the application, copied to user config on first run.
