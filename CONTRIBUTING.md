# Contributing to AI-Hack

Welcome! We're excited you want to contribute to AI-Hack. This project thrives on community contributions, and we appreciate every enhancement, bug fix, and suggestion.

## 🚀 Quick Start for Contributors

### 1. Development Setup

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/kotachisam/aihack.git
cd aihack

# Install development dependencies
poetry install --with dev

# Set up pre-commit hooks (runs linting/formatting automatically)
poetry run pre-commit install

# Verify everything works
poetry run pytest
poetry run ah --help
```

### 2. Making Your First Contribution

```bash
# Create a new branch for your feature/fix
git checkout -b feature/your-feature-name

# Make your changes...

# Run tests and linting
poetry run pytest
poetry run ruff check src/
poetry run mypy src/

# Commit your changes
git add .
git commit -m "feat: add your feature description"

# Push and create a pull request
git push origin feature/your-feature-name
```

## 🎯 Ways to Contribute

### 🐛 Bug Reports

Found a bug? We want to hear about it!

- **Search existing issues** first to avoid duplicates
- **Use our bug report template** when creating new issues
- **Include reproduction steps** and your environment details
- **Add the `bug` label** to your issue

### ✨ Feature Requests

Have an idea to make AI-Hack better?

- **Check our [BUILD_PLAN.md](BUILD_PLAN.md)** to see if it's already planned
- **Use our feature request template** for new suggestions
- **Explain the use case** and why it would be valuable
- **Consider privacy implications** of your request

### 🔧 Code Contributions

Ready to dive into the code?

**High-Impact Areas:**

- **Model Integrations**: Add support for new local or cloud models
- **Privacy Features**: Enhance content classification and routing
- **CLI Experience**: Improve Rich terminal interfaces
- **Performance**: Optimize async operations and caching
- **Testing**: Add comprehensive test coverage

### 📚 Documentation

Help make AI-Hack more accessible:

- **API Documentation**: Document CLI commands and options
- **Tutorials**: Create guides for common use cases
- **Examples**: Add practical code examples
- **README**: Improve setup and usage instructions

## 🏗️ Development Guidelines

### Code Style

We use automated formatting and linting:

```bash
# Format code
poetry run black src/ tests/
poetry run isort src/ tests/

# Check for issues
poetry run ruff check src/ tests/
poetry run mypy src/

# Run all checks (pre-commit hook does this automatically)
poetry run pre-commit run --all-files
```

### Project Structure

```text
src/aihack/
├── cli/          # Command-line interface
├── models/       # AI model integrations
├── core/         # Core orchestration logic
├── safety/       # Security and privacy features
├── types/        # Type definitions
├── prompts/      # Model-specific prompts
└── tests/        # Test files
```

### Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test model interactions and CLI commands
- **Mock External APIs**: Never make real API calls in tests
- **Test Privacy Features**: Ensure sensitive content stays local

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=aihack

# Run specific test file
poetry run pytest src/aihack/tests/models/testclaude.py -v
```

### Privacy-First Development

AI-Hack's core value is privacy. When contributing:

- **Local by Default**: New features should work locally when possible
- **Explicit Cloud Usage**: Make cloud API usage obvious to users
- **Content Classification**: Help improve sensitive content detection
- **Security Review**: Consider security implications of changes

## 🚦 Pull Request Process

### Before Submitting

- [ ] **Tests pass**: `poetry run pytest`
- [ ] **Code is formatted**: Pre-commit hooks handle this
- [ ] **Types are correct**: `poetry run mypy src/`
- [ ] **Documentation updated**: If you changed APIs or behavior
- [ ] **Privacy impact considered**: Note any privacy implications

### PR Requirements

1. **Descriptive Title**: Use conventional commit format (feat:, fix:, docs:, etc.)
2. **Clear Description**: Explain what your PR does and why
3. **Link to Issue**: Reference the issue your PR addresses (if applicable)
4. **Test Coverage**: Add tests for new functionality
5. **Breaking Changes**: Mark breaking changes clearly

### Review Process

1. **Automated Checks**: CI runs tests, linting, and type checking
2. **Code Review**: Maintainers review for code quality and design
3. **Privacy Review**: Special attention to privacy and security implications
4. **Testing**: Manual testing for complex changes
5. **Merge**: Once approved, we'll merge your contribution!

## 🌟 Recognition

We believe in recognizing our contributors:

- **Contributor List**: All contributors are acknowledged in our README
- **Release Notes**: Significant contributions are highlighted in releases
- **Contributor Badges**: GitHub profile badges for sustained contributions
- **Maintainer Track**: Active contributors can become maintainers

## 🤝 Community Guidelines

### Code of Conduct

We're committed to providing a welcoming, inclusive environment:

- **Be Respectful**: Treat all community members with respect
- **Be Collaborative**: We're all working toward the same goal
- **Be Patient**: Remember that people have different skill levels
- **Be Constructive**: Focus on solutions, not problems

### Communication

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general conversation
- **Pull Requests**: For code contributions and reviews

### Getting Help

New to contributing? We're here to help!

- **Good First Issues**: Look for issues labeled `good-first-issue`
- **Mentorship**: Maintainers are happy to guide new contributors
- **Documentation**: Check our docs and examples
- **Community**: Ask questions in GitHub Discussions

## 🔒 Security

Found a security vulnerability? Please **don't** open a public issue. Instead:

1. **Email us privately** (when available) or use GitHub's private vulnerability reporting
2. **Include details** about the vulnerability and how to reproduce it
3. **Wait for our response** before disclosing publicly
4. **Work with us** to fix the issue responsibly

See our [Security Policy](.github/SECURITY.md) for full details.

## 📋 Development Checklist

Before submitting your contribution:

### Code Quality

- [ ] Code follows project conventions
- [ ] All tests pass locally
- [ ] New functionality is tested
- [ ] Code is documented where needed
- [ ] No sensitive information in code/commits

### Privacy & Security

- [ ] Changes maintain privacy-first principles
- [ ] No hardcoded secrets or API keys
- [ ] Input validation added where needed
- [ ] Security implications considered

### Documentation

- [ ] README updated if needed
- [ ] Breaking changes documented
- [ ] API changes documented
- [ ] Examples updated if applicable

## 🙏 Thank You

Every contribution makes AI-Hack better for developers worldwide. Whether you're fixing a typo, adding a feature, or improving documentation, your work helps create better, more private development tools.

**Ready to contribute?** Check out our [open issues](https://github.com/kotachisam/aihack/issues) or [BUILD_PLAN.md](BUILD_PLAN.md) for inspiration!

---

*Questions? Open a [GitHub Discussion](https://github.com/kotachisam/aihack/discussions) and we'll help you get started.*
