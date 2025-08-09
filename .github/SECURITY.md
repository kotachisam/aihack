# Security Policy

## 🔒 Our Security Commitment

AI-Hack takes security seriously. As a privacy-first development tool that handles sensitive code and integrates with AI models, we're committed to maintaining the highest security standards.

## 🛡️ Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ Active support  |
| < 0.1   | ❌ No support      |

## 🚨 Reporting Security Vulnerabilities

**Please DO NOT report security vulnerabilities through public GitHub issues.**

### Preferred Reporting Method

1. **Email**: Send details to `security@aihack.dev` (if available)
2. **Private Security Advisory**: Use GitHub's private vulnerability reporting
3. **Direct Contact**: Reach out to maintainers privately

### What to Include

When reporting a security vulnerability, please include:

- **Type of vulnerability** (e.g., injection, authentication bypass, etc.)
- **Full paths of source files** related to the vulnerability
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if available)
- **Impact assessment** - how an attacker might exploit this
- **Suggested fix** (if you have one)

### Response Timeline

- **Initial response**: Within 48 hours
- **Progress updates**: Every 7 days until resolution
- **Resolution target**: 90 days for critical issues, 120 days for others

## 🎯 Security Scope

### In Scope
- Authentication and authorization flaws
- Code injection vulnerabilities
- API key/secret exposure
- Privilege escalation
- Data validation issues
- Privacy breaches in AI model routing
- Dependency vulnerabilities

### Out of Scope
- Social engineering attacks
- Physical security
- Issues requiring admin access to the system
- Third-party service vulnerabilities (Claude, Gemini APIs)
- Issues in unsupported versions

## 🔐 Security Best Practices

### For Users
- **Never commit API keys** to version control
- **Use environment variables** for sensitive configuration
- **Regularly update** AI-Hack to the latest version
- **Review privacy settings** before processing sensitive code
- **Monitor API usage** for unusual activity

### For Contributors
- **Follow secure coding practices** outlined in CONTRIBUTING.md
- **Validate all inputs** from users and external APIs
- **Use parameterized queries** for any database operations
- **Implement proper error handling** without information disclosure
- **Review dependencies** for known vulnerabilities

## 🧪 Security Testing

We encourage security researchers to:
- **Responsibly test** our software
- **Follow coordinated disclosure** practices
- **Respect user privacy** during testing
- **Test only on your own systems** or with explicit permission

## 🏆 Recognition

We appreciate security researchers who help keep AI-Hack secure:
- **Security Hall of Fame** (when established)
- **Public acknowledgment** (with your permission)
- **Swag and rewards** for critical findings (when program launches)

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Guide](https://python-security.readthedocs.io/)
- [AI Security Best Practices](https://owasp.org/www-project-ai-security-and-privacy-guide/)

## 📞 Contact Information

- **Security Team**: `security@aihack.dev`
- **General Contact**: `hello@aihack.dev`
- **GitHub**: Open a private security advisory

---

**Remember**: AI-Hack processes your code locally by default. Always verify privacy settings before processing sensitive information.
