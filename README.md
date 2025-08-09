# AI-Hack: Your Privacy-First AI Coding Partner 🚀

**Develop with the power of AI without ever compromising on privacy. AI-Hack intelligently routes your requests to local or cloud models, ensuring your sensitive code never leaves your machine.**

[![GitHub stars](https://img.shields.io/github/stars/kotachisam/aihack?style=social)](https://github.com/kotachisam/aihack/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/kotachisam/aihack)](https://github.com/kotachisam/aihack/issues)
[![GitHub license](https://img.shields.io/github/license/kotachisam/aihack)](https://github.com/kotachisam/aihack/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## The Problem: Privacy vs. Intelligence

Current AI coding tools force an impossible choice:

- **Privacy**: Keep your code 100% local, but miss out on the most powerful AI models.
- **Intelligence**: Use cutting-edge cloud-based AI, but send your proprietary code to third-party servers.

## Our Solution: The Best of Both Worlds

AI-Hack is the first tool designed from the ground up to solve this dilemma. It acts as a smart, privacy-aware layer between you and your AI models.

- ✅ **Privacy + Intelligence**: Smart hybrid processing keeps sensitive data local.
- ✅ **Speed + Quality**: Use the right model for the right task, from fast local analysis to deep cloud-powered reviews.
- ✅ **Simple + Capable**: A single, intuitive CLI (`ah`) gives you access to a world of AI capabilities.

<!-- TODO: Add a GIF demo of the interactive session or a key command -->

## Core Features

- **🔒 Privacy-First by Default**: All analysis is performed locally unless you explicitly request a cloud model.
- **🤖 Multi-Model Support**: Seamlessly switch between local models (like CodeLlama or Mixtral via Ollama) and cloud APIs (Gemini, Claude).
- **🛡️ Smart Security Engine**: Automatically routes requests based on content sensitivity and your privacy settings.
- **⚡ Powerful CLI (`ah`)**: A single, consistent interface for all your AI-assisted development tasks: `review`, `analyze`, `refactor`, `compare`, and more.
- **🎭 Model Comparison**: Run your code against multiple models simultaneously and see a side-by-side comparison of their analyses.

## 🚀 Getting Started

Ready to try it? Our detailed **[GETTING_STARTED.md](GETTING_STARTED.md)** guide will have you up and running in less than 5 minutes.

```bash
# 1. Clone the repo
git clone https://github.com/kotachisam/aihack.git
cd aihack

# 2. Install dependencies
poetry install

# 3. Activate the environment
poetry shell

# 4. Run your first command!
ah review examples/simple_logic.py --model local
```

## 🤝 Join the Revolution

We're not just building a tool—we're creating the future of privacy-conscious development. And we need your help.

### How You Can Contribute

- 🌟 **Star the Repo**: It’s the easiest way to show your support!
- 🐛 **Report Issues**: Find a bug? [Open an issue](https://github.com/kotachisam/aihack/issues).
- 💡 **Suggest Features**: Have a great idea? [Submit a feature request](https://github.com/kotachisam/aihack/issues/new?assignees=&labels=enhancement%2C+needs-triage&template=feature_request.yml&title=%5BFeature%5D%3A+).
- 🔧 **Contribute Code**: Ready to dive in? Read our **[CONTRIBUTING.md](CONTRIBUTING.md)** to get started.

We have a special focus on a few high-impact areas perfect for new contributors:

- **🤖 Model Integrations**: Add support for new local or cloud models.
- **🎨 User Experience**: Help us improve the CLI output and build new features.
- **🔒 Privacy & Security**: Enhance our content classification and security scanning rules.

### Our Community

We are committed to fostering a welcoming and inclusive environment. All contributors are expected to adhere to our **[Code of Conduct](CODE_OF_CONDUCT.md)**.

## 📜 License

AI-Hack is licensed under the [MIT License](LICENSE).
