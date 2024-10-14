# CaptionCreator

**CaptionCreator** is a tool that converts audio files into captioned videos and publishes them to social media platforms. Follow the steps below to get started.

## Prerequisites

- Bun (for running the JavaScript form)
- Python 3 (for audio to video conversion and publishing)
- Required libraries for both Node.js and Python (see installation instructions below)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CaptionCreator

   To Run
    1) run js form
      cd CaptionCreator/ContentData
      bun run index.ts

    2) run audio to caption video converter
      cd CaptionCreator
      python3 audiotovideo.py

    3) run publisher to push to social media
      cd CaptionCreator
      python3 publish_to_socialmedia.py
   ```
