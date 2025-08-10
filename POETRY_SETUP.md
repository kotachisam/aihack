# Poetry Setup Guide for AI-Hack

This guide helps you set up Poetry correctly for AI-Hack development, especially on macOS where LibreSSL/OpenSSL compatibility issues can cause problems.

## Quick Setup (Recommended)

```bash
# 1. Clone and enter the repository
git clone https://github.com/kotachisam/aihack.git
cd aihack

# 2. Run our setup script (handles all the complexity)
./scripts/setup.sh
```

If the setup script works, you're done! If not, continue with the troubleshooting guide below.

## Manual Setup & Troubleshooting

### Step 1: Install Poetry Correctly

**❌ Don't install via pip** - this can cause LibreSSL issues on macOS:

```bash
# DON'T DO THIS on macOS
pip install poetry
```

**✅ Use the official installer** - this avoids system Python issues:

```bash
# DO THIS instead
curl -sSL https://install.python-poetry.org | python3 -
```

### Step 2: Check Your Poetry Installation

```bash
# Check if Poetry is working
poetry --version

# Check which Poetry you're using
which poetry
```

**Expected good output:**

```bash
Poetry (version 2.1.x)
/Users/your-username/.local/bin/poetry
```

**Bad signs:**

- Path shows `/Library/Python/3.9/bin/poetry` (pip-installed)
- Import errors or urllib3 warnings when running `poetry --version`

### Step 3: Fix Multiple Poetry Installations

If you have multiple Poetry installations, find them:

```bash
# Find all Poetry executables
which -a poetry

# Test each one
/Users/your-username/.local/bin/poetry --version
/usr/local/bin/poetry --version  # May be broken
```

**Fix your PATH** to prioritize the working Poetry:

```bash
# Add to your ~/.zshrc or ~/.bash_profile
export PATH="/Users/$(whoami)/.local/bin:$PATH"

# Reload your shell
source ~/.zshrc  # or ~/.bash_profile
```

### Step 4: Handle urllib3 LibreSSL Issues

macOS uses LibreSSL instead of OpenSSL, which urllib3 v2+ doesn't support.

**Test if you have the issue:**

```bash
poetry --version
# If you see urllib3 warnings, you have the issue
```

**Fix it** (only after confirming Poetry works):

```bash
# Downgrade Poetry's urllib3 to compatible version
poetry self add urllib3==1.26.15
```

**⚠️ Warning:** If this breaks Poetry, see recovery steps below.

### Step 5: Install AI-Hack Dependencies

```bash
# Install project dependencies
poetry install

# Test installation
poetry run ah --help
```

## Recovery Procedures

### If Poetry Breaks After urllib3 Fix

- **Find your working Poetry:**

```bash
find /Users -name poetry -type f 2>/dev/null
```

- **Try alternative Poetry installations:**

```bash
/Users/your-username/.local/bin/poetry --version
~/.local/bin/poetry --version
```

- **Reinstall Poetry if needed:**

```bash
# Remove broken Poetry
rm -rf ~/.local/share/pypoetry

# Reinstall
curl -sSL https://install.python-poetry.org | python3 -
```

- **Update your PATH:**

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### If setup.sh Fails

The setup script is designed to be safe, but if it fails:

1. **Check Poetry health first:**

   ```bash
   poetry --version
   poetry env info
   ```

2. **Manually install dependencies:**

   ```bash
   poetry install
   ```

3. **Skip urllib3 fix initially:**

   ```bash
   # Just run the app - warnings are harmless
   poetry run ah --help
   ```

4. **Apply urllib3 fix carefully:**

   ```bash
   # Backup Poetry first
   cp -r ~/.local/share/pypoetry ~/.local/share/pypoetry.backup

   # Try the fix
   poetry self add urllib3==1.26.15

   # Test Poetry still works
   poetry --version
   ```

## Common Error Messages

### "ImportError: No module named 'requests'"

- Your Poetry installation is broken
- Follow the recovery procedures above
- Usually means urllib3 downgrade broke Poetry

### "NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+"

- This is the LibreSSL compatibility issue
- The warning is harmless but annoying
- Apply the urllib3 fix in Step 4

### "poetry: command not found"

- Poetry isn't installed or not in PATH
- Install using the official installer
- Add `~/.local/bin` to your PATH

### "Could not find a matching version of package urllib3"

- Your Poetry version might be too old
- Update Poetry: `poetry self update`
- Or use a different urllib3 version

## Platform Notes

### macOS (Primary Support)

- LibreSSL compatibility issues are common
- Use Homebrew Python if system Python causes issues
- Official Poetry installer works best

### Linux (Planned)

- Should work without urllib3 issues
- Standard Poetry installation should suffice
- Not yet tested - feedback welcome!

### Windows (Planned)

- Not yet tested
- Poetry installation should be straightforward
- urllib3 issues unlikely

## Getting Help

If you're still having trouble:

1. **Check the GitHub issues:** [Issues](https://github.com/kotachisam/aihack/issues)
2. **Create a new issue** with:
   - Your OS version
   - `poetry --version` output
   - `which -a poetry` output
   - Full error messages
3. **Include Poetry environment info:**

   ```bash
   poetry env info
   ```

## Contributing to This Guide

Found a solution to a problem not covered here? Please contribute:

1. Test your solution thoroughly
2. Update this guide with clear steps
3. Submit a pull request

This guide is a living document that improves with community input!
