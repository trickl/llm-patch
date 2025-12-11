# Toolchain Setup

The failure-generation scripts expect the following runtimes/compilers to be available locally. Commands below target Ubuntu/Debian systems; adapt as needed for macOS or other Linux distributions.

## Common Prerequisites

1. **Python 3.10+** – already required for `llm-patch` development.
2. **Ollama** – install from https://ollama.com/download and ensure `ollama` is on your PATH. Verify with:
   ```bash
   ollama list
   ```
3. **Model pulls** – prefetch required models to avoid repeated downloads:
   ```bash
   ollama pull qwen2.5-coder:7b
   ollama pull llama3.2:3b
   ollama pull phi3:mini
   ```

## Language-Specific Tooling

### Java
```bash
sudo apt-get update
sudo apt-get install -y openjdk-21-jdk
```
Verify: `javac -version`

### C / C++
```bash
sudo apt-get install -y build-essential
```
Verify: `gcc --version` and `g++ --version`

### TypeScript
```bash
sudo apt-get install -y nodejs npm
sudo npm install -g typescript
```
Verify: `tsc --version`

### Python (lint-only mode)
We rely on the standard library’s `py_compile` for syntax validation. No extra packages required.

## Troubleshooting

- Missing toolchains will surface as `FileNotFoundError` from the generator script; install the dependency and rerun.
- Some distributions name packages differently (e.g., `jdk` vs. `openjdk`). Adjust commands accordingly.
- Ensure adequate disk space—capturing hundreds of raw LLM generations produces sizable artifacts.
