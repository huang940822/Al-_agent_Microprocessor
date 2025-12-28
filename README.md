# Learning Agent
## Setup
* First, follow these [instructions](https://github.com/ollama/ollama?tab=readme-ov-file#ollama) to set up and run a local Ollama instance:
[Download](https://ollama.com/download) and install Ollama onto the available supported platforms (including Windows Subsystem for Linux aka WSL, macOS, and Linux)
  * macOS users can install via Homebrew with ```brew install ollama``` and start with ```brew services start ollama```
* Fetch available LLM model via ```ollama pull <name-of-model>```
 * View a list of available models via the model [library](https://ollama.com/library)
 * e.g., ```ollama pull gpt-oss:20b```
*This will download the default tagged version of the model. Typically, the default points to the latest, smallest sized-parameter model.
[!NOTE]
On Mac, the models will be download to ```~/.ollama/models```
[!NOTE]
On Linux (or WSL), the models will be stored at ```/usr/share/ollama/.ollama/models```
