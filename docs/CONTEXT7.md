# Context7 documentation log

Library/API documentation was retrieved through
**Context7** (`https://context7.com`) rather than relying on recall. The
model-specific deployment details (GGUF names, mmproj, prompts) come from the
official OpenBMB/MiniCPM repositories, because Context7 indexes library docs,
not model weights or model cards.

## Libraries queried

| Library | Context7 ID | Topics | Used for |
|---|---|---|---|
| FastAPI | `/websites/fastapi_tiangolo` | request handling, file uploads, response models | API design |
| llama.cpp | `/ggml-org/llama.cpp` | server, multimodal chat completions, grammar/JSON | local model serving |
| React | `/reactjs/react.dev` | hooks, state, effects | Web UI |
| Playwright | `/microsoft/playwright` | screenshots, video, browser context | desktop demo/recordings |
| WeasyPrint | `/kozea/weasyprint` | HTML/CSS → PDF | evidence ledger PDF |
| OpenCV | `/opencv/opencv` | Hough lines, image quality | valve angle / quality |
| FFmpeg | `/websites/ffmpeg_documentation` | concat, overlay, subtitles | video production |

## Queries used

```bash
curl 'https://context7.com/api/v1/search?query=llama.cpp'
curl 'https://context7.com/api/v1/ggml-org/llama.cpp?tokens=2500&topic=server%20multimodal%20chat%20completions%20grammar%20json'
curl 'https://context7.com/api/v1/reactjs/react.dev?tokens=2500&topic=hooks%20useEffect%20state'
curl 'https://context7.com/api/v1/microsoft/playwright?tokens=2500&topic=screenshot%20video%20record'
curl 'https://context7.com/api/v1/kozea/weasyprint?tokens=2500&topic=pdf%20html%20css'
curl 'https://context7.com/api/v1/opencv/opencv?tokens=2500&topic=hough%20lines%20detect'
curl 'https://context7.com/api/v1/websites/ffmpeg_documentation?tokens=2500&topic=concat%20filter%20overlay%20subtitles'
```

## Notes

- Context7 search results were used to confirm the current llama.cpp
  `/v1/chat/completions` multimodal shape, React hook patterns, Playwright
  recording options, WeasyPrint PDF usage, OpenCV `HoughLinesP`, and FFmpeg
  filter graphs.
- The actual GGUF filenames, mmproj requirements, Q4/Q8 sizes, and the
  `Text Recognition:` prompt were verified against the official
  [MiniCPM-V](https://github.com/OpenBMB/MiniCPM-V),
  [MiniCPM-OCR](https://github.com/OpenBMB/MiniCPM-OCR), and
  [MiniCPM-V-Apps](https://github.com/OpenBMB/MiniCPM-V-Apps) repositories.
- APIs change; pin versions in `server/requirements.txt` and `web/package.json`
  when reproducing.
