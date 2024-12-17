# Security Policy

## Supported Versions

Currently being supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Solana Token Scanner Bot seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email or through a private channel. You can expect to receive a response within 48 hours.

Please include the following information:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Best Practices

When using this bot:

1. **Private Keys**
   - Never share your private keys
   - Store private keys securely
   - Use environment variables for sensitive data
   - Never commit .env files

2. **RPC Endpoints**
   - Use trusted RPC providers
   - Consider rate limits
   - Monitor for unusual activity

3. **Wallet Security**
   - Use a dedicated wallet for the bot
   - Monitor wallet activity
   - Set appropriate transaction limits

4. **Network Security**
   - Use secure connections
   - Implement proper error handling
   - Monitor for suspicious activities

5. **Dependencies**
   - Keep dependencies updated
   - Review dependency security alerts
   - Use locked versions in requirements.txt

## Updates and Security Patches

- Security updates will be released as soon as possible
- Users will be notified through GitHub releases
- Critical updates will be highlighted in the README

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find any similar problems
3. Prepare fixes for all supported versions
4. Release new versions/patches

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a pull request. 