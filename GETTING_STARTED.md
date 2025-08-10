# 🚀 Getting Started with AI-Hack: Your Privacy-First AI Coding Partner

Welcome to AI-Hack! This guide provides a detailed walkthrough to get you from zero to hero, empowering you with AI while ensuring your code remains private.

**Our Mission**: To make advanced AI-assisted development universally accessible without ever compromising on privacy.

---

## 1. Prerequisites

Before you begin, ensure you have the following installed:

* **Python**: Version 3.11 or newer (3.13 recommended).
* **Git**: For cloning the repository.
* **Poetry**: For managing dependencies and the virtual environment.

**⚠️ Platform Support**: AI-Hack is currently tested on **macOS only**. Linux and Windows support is planned but not yet tested.

### Poetry Installation (Critical for macOS)

**For the best experience on macOS**, install Poetry using the official installer (NOT pip):

```bash
# Install Poetry (recommended for macOS)
curl -sSL https://install.python-poetry.org | python3 -
```

**Why not pip?** Installing Poetry via pip on macOS can cause LibreSSL compatibility issues that lead to urllib3 warnings. The official installer avoids these problems.

---

## 2. Installation & Setup

Follow these steps carefully to set up your environment.

### Step 1: Clone the Repository

Open your terminal and clone the AI-Hack repository from GitHub.

```bash
git clone https://github.com/kotachisam/aihack.git
cd aihack
```

### Step 2: Run the Setup Script (Recommended)

Use our automated setup script that handles Poetry issues and macOS compatibility:

```bash
./setup.sh
```

This script will:

* Detect and fix Poetry installation issues
* Apply macOS urllib3 compatibility fixes
* Install all dependencies
* Test your installation

### Alternative: Manual Installation

If you prefer manual installation or the setup script fails:

```bash
# Install dependencies
poetry install

# Fix macOS urllib3 warnings (if needed)
poetry self add urllib3==1.26.15

# Test installation
poetry run ah --help
```

**If you encounter Poetry issues**, see our comprehensive **[POETRY_SETUP.md](POETRY_SETUP.md)** troubleshooting guide.

### 💥 Step 3: Activate the Virtual Environment (Crucial!)

To use the `ah` command-line tool, you must first activate the virtual environment that Poetry just created.

**Recommended Method: `poetry shell`**

This command spawns a new shell session with the virtual environment activated. You only need to do this once per terminal session.

```bash
poetry shell
```

You'll know it worked when you see your terminal prompt change to something like `(aihack-py3.11)`. Now you can run `ah` directly.

**Alternative Method: `poetry run`**

If you prefer not to start a new shell, you can prefix every `ah` command with `poetry run`.

```bash
poetry run ah --help
```

---

## 3. Configuration (API Keys for Cloud Models)

AI-Hack works with local models out-of-the-box. To unlock the power of cloud models like **Gemini** and **Claude**, you need to provide API keys.

AI-Hack loads these keys from a `.env` file in the project root.

### Step 1: Create the `.env` File

Create a new file named `.env` in the `aihack` directory.

```bash
touch .env
```

### Step 2: Add Your API Keys

Open the `.env` file and add your keys like this:

```env
# .env file
GOOGLE_API_KEY="your_google_api_key_here"
CLAUDE_API_KEY="your_anthropic_api_key_here"
```

*AI-Hack will never share these keys. They are loaded locally to communicate with the APIs.*

---

## 4. Your First Commands: A Guided Tour

Let's see AI-Hack in action! First, create a sample Python file to work with.

**Create a test file:**

```bash
echo '''
import os

def get_user_data(user_id):
    # In a real app, this would fetch from a database
    if user_id == 1:
        return {"name": "Alice", "email": "alice@example.com"}
    return None

def process_file(filename):
    # This is insecure!
    data = open(filename, "r").read()
    print(f"Processing {len(data)} bytes")
''' > example.py
```

Now, let's use `ah` (ensure you've run `poetry shell` first!).

### Example 1: Local Code Analysis (100% Private)

Analyze the structure of your new file. This command runs entirely on your machine.

```bash
ah hack example.py --task analyze
```

**Expected Output**: You will see a structured analysis of the functions, imports, and potential improvements in `example.py`, printed directly to your terminal.

### Example 2: Secure Refactoring

Ask AI-Hack to refactor the code, forcing it to use a local model to guarantee privacy.

```bash
ah hack example.py --task refactor --privacy=high
```

**Expected Output**: AI-Hack will suggest a safer way to write the `process_file` function, likely using a `with open(...)` block to ensure the file is properly closed.

### Example 3: Cloud-Powered Security Review

Use a powerful cloud model to find deeper issues. This requires a configured API key.

```bash
ah review example.py --model gemini --focus security
```

**Expected Output**: The Gemini model will perform a security review and likely flag the `process_file` function as a potential vulnerability (e.g., lack of error handling, path traversal risk).

### Example 4: Compare Models Side-by-Side

See how different AI models analyze the same code. This is perfect for choosing the best tool for the job.

```bash
ah compare --models=local,gemini example.py
```

**Expected Output**: A side-by-side table in your terminal showing the analysis from both the local model and Gemini, allowing you to compare their findings directly.

---

## 5. Troubleshooting

### Common Issues

* **`ah: command not found`**: You forgot to activate the virtual environment. Run `poetry shell` in the project directory and try again.
* **Cloud Model Errors**: If you get an authentication error, double-check that your `.env` file is correctly named and that your API keys are accurate.
* **urllib3 warnings on macOS**: This is a LibreSSL compatibility issue. Run `poetry self add urllib3==1.26.15` to fix.
* **Poetry broken after urllib3 fix**: See the recovery procedures in **[POETRY_SETUP.md](POETRY_SETUP.md)**.

### Getting Help

If you're still having trouble:

1. **Check the comprehensive Poetry troubleshooting guide**: **[POETRY_SETUP.md](POETRY_SETUP.md)**
2. **Search existing issues**: [GitHub Issues](https://github.com/kotachisam/aihack/issues)
3. **Create a new issue** with your OS version, Poetry version, and full error messages

---

## 6. What's Next?

You've just scratched the surface!

* **Dive Deeper**: Read our full **[README.md](README.md)** for the project's vision and a comprehensive feature list.
* **Become a Contributor**: Check out **[CONTRIBUTING.md](CONTRIBUTING.md)** to see how you can help build the future of AI development.
* **Report Issues**: Found a bug or have a feature request? **[Open an issue](https://github.com/kotachisam/aihack/issues)**.
