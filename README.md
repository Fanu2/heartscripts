# ❤️ HeartScript Studio

> **A local-first AI co-writing workbench for novels, romance, dialogue, screenwriting, and courseware — powered by any suitable LLM.**

HeartScript Studio is a lightweight desktop application built with **Python and PySide6**. It is designed as a **human + AI co-writing environment**, where the writer remains in control while AI assists with writing, dialogue, scenes, chapters, ideas, and educational content.

The application is inspired by the idea of an AI writing workbench with live generation, project organization, editable context, and support for multiple AI models.

---

## ✨ Features

### 📁 Project Management

Create and manage different types of writing projects:

- 📖 Novel
- ❤️ Romance
- 🎬 Dialogue
- 🎭 Screenwriting
- 📚 Courseware

Projects are stored locally and organized into chapters.

---

## ✍️ Writing Studio

The central writing workspace provides:

- Chapter editor
- Editable chapter titles
- Local saving
- AI-generated text insertion
- Chapter organization
- Human editing at any time

The writer always has control over the final content.

---

## 🤖 AI Co-Writing

HeartScript Studio is designed to support multiple LLM providers.

### Initial support

- 🦙 Ollama local models
- 🌐 OpenAI-compatible APIs
- ☁️ Cloud AI providers
- 💻 Local AI servers

Examples of possible models include:

- Qwen
- Llama
- DeepSeek
- Mistral
- Gemma
- Other Ollama-compatible models
- Any OpenAI-compatible API

The architecture is intended to avoid locking the application to a single AI provider.

---

## ⚡ Live AI Console

AI output appears live while it is being generated.

The console is intended to support:

- Live streaming text
- Pause generation
- Stop generation
- Resume generation
- Regenerate output
- Insert generated text into a chapter
- Edit generated content
- Rewrite individual sections

Example:

```text
AI CONSOLE
────────────────────────────────────

Maya looked toward the window.

The rain had finally stopped, but neither
of them had moved.

Daniel wanted to say something.

Anything.

[Generating...]

▌

────────────────────────────────────
[ Pause ] [ Stop ] [ Regenerate ]
