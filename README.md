# Learning Agent
## Setup
* First, follow these [instructions](https://github.com/ollama/ollama?tab=readme-ov-file#ollama) to set up and run a local Ollama instance:
[Download](https://ollama.com/download) and install Ollama onto the available supported platforms (including Windows Subsystem for Linux aka WSL, macOS, and Linux)
  * macOS users can install via Homebrew with ```brew install ollama``` and start with ```brew services start ollama```
* Fetch available LLM model via ```ollama pull <name-of-model>```
 * View a list of available models via the model [library](https://ollama.com/library)
 * e.g., ```ollama pull gpt-oss:20b```
* This will download the default tagged version of the model. Typically, the default points to the latest, smallest sized-parameter model.
>[!NOTE]
>On Mac, the models will be download to ```~/.ollama/models```
>
>On Linux (or WSL), the models will be stored at ```/usr/share/ollama/.ollama/models```
* Specify the exact version of the model of interest as such ollama pull gpt-oss:20b (View the [various tags for the Vicuna](https://ollama.com/library/vicuna/tags) model in this instance)
* To view all pulled models, use ```ollama list```
* To chat directly with a model from the command line, use ```ollama run <name-of-model>```
* View the [Ollama documentation](https://github.com/ollama/ollama/blob/main/docs/README.md) for more commands. You can run ```ollama help``` in the terminal to see available commands.

## Environment
