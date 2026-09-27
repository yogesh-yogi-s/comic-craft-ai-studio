# Comic Craft Giri - AI Comic Story Creator

Comic Craft Giri (CCG) is an end-to-end AI comic studio that turns character ideas, loose prompts, and wild scenarios into complete 5-panel comic book stories, character dialogues, narrative captions, and stylized illustrations.

Built with **FastAPI**, **Google Gemini AI**, **Multi-Tier Comic Illustration Engines**, and **FPDF2**, Comic Craft Giri provides an authentic comic studio workflow from prompt creation to multi-page PDF comic export with Day/Night mode theming.

---

## Technical Architecture

```
User Scenario & Preferences
         │
         ▼
[ FastAPI Backend: app/routes.py ]
         │
         ├──► 1. [ app/gemini_flash.py ]  ──► Structured 5-panel outline & scene prompts
         ├──► 2. [ app/gemini_pro.py ]    ──► Narration, SFX captions, character dialogues
         ├──► 3. [ app/image_generator.py]──► Multi-tier AI & scene artwork illustrations
         ├──► 4. [ app/layout_builder.py] ──► Sequential 5-panel comic data layout
         └──► 5. [ app/exporters.py ]     ──► Multi-page styled comic book PDF
         │
         ▼
[ Studio Frontend: templates/comic_preview.html / export_success.html ]
```

### Models & Services Used
- **Google Gemini Flash (`models/gemini-3.8-flash` / `models/gemini-flash-latest`)**: Rapid, structured generation of the 5-panel comic outline and scene prompts with prompt-aware fallback.
- **Google Gemini Pro (`models/gemini-3.8-flash` / `models/gemini-pro-latest`)**: Narrative storytelling, character dialogues, and atmospheric sound effect captions (SFX).
- **Multi-Tier Comic Illustration Engine (`app/image_generator.py`)**: 
  - **Tier 1**: Cloud AI text-to-image generator producing vivid 768x512 comic book artwork matching the exact characters and setting.
  - **Tier 2**: Keyword-driven scene artwork engine ensuring every single panel has full visual artwork without blank canvases or rate-limit dropouts.
  - **Tier 3**: Local Diffusers & graphic studio renderer.
- **FPDF2 Exporter (`app/exporters.py`)**: Assembles comic cover art, sequential panels, speech bubbles, and narrative captions into a downloadable PDF.
- **Studio Frontend (`templates/`, `static/`)**: Authentic CCG studio aesthetic with tilted crimson wordmark stamp, Day & Night mode theming, and responsive layout.

---

## Rich Scenario & Setting Options

The studio form includes diverse curated presets plus custom options:

### 1. Curated Settings
- **Hidden Leaf Village & Ichiraku Ramen Shop** *(Anime / Ninja)*
- **Cyberpunk Metropolis & Neon Alleys** *(Neo-Tokyo / Sci-Fi)*
- **Enchanted Ancient Forest** *(High Fantasy)*
- **Deep Space Starship Cruiser** *(Galactic)*
- **Gothic City Rooftops** *(Dark Noir / Detective)*
- **Haunted Victorian Academy** *(Supernatural)*
- **Steampunk Airship Citadel** *(Adventure)*
- **Post-Apocalyptic Wasteland** *(Survival)*
- **Sunken Atlantis Ruins** *(Underwater Empire)*
- **Feudal Samurai Dojo** *(Martial Arts)*
- **Ancient Dragon Peak** *(Mythic)*
- **Custom Setting** *(Write your own custom world)*

### 2. Story Tones
- **Action Shonen**
- **Epic Adventure**
- **Funny & Humorous**
- **Dramatic**
- **Light-hearted & Whimsical**
- **Dark Mystery & Noir**
- **Poetic & Atmospheric**

### 3. Art Styles
- **Shonen Manga / Anime**
- **Classic DC/Marvel Comic Book**
- **Dark Graphic Novel (Noir Ink)**
- **Cyberpunk Neon**
- **Vintage 1980s Pulp Comic**
- **Watercolor Fantasy**
- **Pixel Art Retro**

---

## Directory Structure

```
Comic Craft Giri/
├── .env.example              # Environment variables template
├── .env                      # Local environment configuration
├── requirements.txt          # Python dependencies
├── README.md                 # Complete documentation & setup guide
├── .vscode/
│   ├── launch.json           # VS Code debug & run configurations
│   ├── settings.json         # Workspace settings & test discovery
│   └── extensions.json       # Recommended VS Code extensions
├── app/
│   ├── __init__.py           # App package
│   ├── main.py               # FastAPI entry point & directory startup
│   ├── routes.py             # Route handlers (/, /generate, /generate-comic/json, etc.)
│   ├── gemini_flash.py       # Outline generation service
│   ├── gemini_pro.py         # Narration & dialogue script generator
│   ├── image_generator.py    # Multi-tier comic illustration engine
│   ├── layout_builder.py     # Layout assembly service
│   └── exporters.py          # Multi-page PDF generation engine
├── static/
│   ├── css/
│   │   ├── style.css         # CCG studio styling & Day/Night theming
│   │   └── comic.css         # Comic frames, speech bubbles & layout styles
│   ├── js/
│   │   └── app.js            # Prompt chips, theme toggle & generation stepper
│   ├── panels/               # Generated comic panel images (.png)
│   └── exports/              # Compiled comic PDF files (.pdf)
├── templates/
│   ├── index.html            # Main comic generation studio form
│   ├── comic_preview.html    # 5-panel sequential reader & PDF trigger
│   └── export_success.html   # Download confirmation & showcase
└── tests/
    ├── __init__.py
    ├── test_gemini.py        # Gemini service tests
    ├── test_image.py         # Image generator tests
    ├── test_layout.py        # Layout builder & PDF exporter tests
    └── test_routes.py        # FastAPI route integration tests
```

---

## Quick Run Instructions

### 1. Launch with VS Code (1-Click)
1. Open the project in VS Code:
   ```bash
   code "e:\Comic Craft Giri"
   ```
2. Press **`F5`** (or go to **Run and Debug** -> select **"Python: Run ComicCraft Server"**).

### 2. Launch from Terminal
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Open in Browser
- **Studio Interface**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **System Health Status**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Running Automated Tests

Run the full automated test suite:
```powershell
pytest -v
```
All **11 core automated tests** verify:
- Gemini Flash 5-panel outline structure and prompt customization
- Gemini Pro story narration, captions, and character speech dialogues
- Multi-tier image generation and filesystem saving
- Comic layout binding and multi-page PDF compilation
- FastAPI routes (`/`, `/health`, `/generate`, `/generate-comic/json`, `/test-image`, `/export-success`)
