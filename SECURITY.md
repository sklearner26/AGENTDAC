# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing security@aog.dev or through the GitHub Security Advisory system.

We will acknowledge receipt of your report within 48 hours and provide a timeline for resolution.

## Security Best Practices

### For Users

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Use environment variables** for secrets in production
3. **Enable redaction** for sensitive data
4. **Keep SDK updated** for security patches
5. **Review integration permissions** - only grant necessary access

### For Developers

1. **Never log sensitive data** in SDK or backend
2. **Validate all inputs** - use Pydantic validation
3. **Implement proper authentication** for API endpoints
4. **Use parameterized queries** to prevent SQL injection
5. **Keep dependencies updated**
6. **Perform security reviews** before merging

## AOG Security Features

### 1. Data Redaction

- Automatic redaction of common secret patterns
- Configurable redaction rules
- No automatic capture of secrets
- Stack trace redaction available

### 2. Fail-Open Design

- Agent continues operating if AOG is unavailable
- Events buffered or dropped according to configuration
- Application stability prioritized over observability

### 3. Idempotency

- Event ingestion safe to retry
- Primary key on `event_id` prevents duplicates
- Database-level protection against duplicate processing

### 4. Input Validation

- All external payloads validated with Pydantic
- Malformed events rejected at ingestion
- Schema validation for all API endpoints

### 5. Secure by Default

- No secrets stored in plaintext
- API keys required for ingestion (configurable)
- CORS restricted in production
- Rate limiting available via middleware

### 6. Privacy Controls

- Configurable input/output capture
- Customizable redaction rules
- Audit trail for redaction decisions
- GDPR/CCPA compliance considerations

## Secure Configuration

### Environment Variables

Never commit real secrets. Use `.env.example` as template:

```env
# .env.example (safe to commit)
AOG_DATABASE_URL=postgresql+asyncpg://aog:aog@localhost:5432/aog
AOG_API_KEY=dev-key
AOG_LOG_LEVEL=INFO
```

In production `.env` (never commit):

```env
# .env (NEVER commit)
AOG_DATABASE_URL=postgresql+asyncpg://aog:secure-password@prod-db:5432/aog
AOG_API_KEY=your-production-api-key-here
AOG_LOG_LEVEL=WARNING
```

### Docker Secrets

For Docker deployments, consider using Docker secrets or Kubernetes secrets for sensitive values.

## Dependency Security

AOG uses `uv` for dependency management with built-in security features:

- Locked dependencies via `uv.lock`
- Hash verification for packages
- Auditable dependency tree
- Regular dependency updates recommended

## Incident Response

If you discover a security issue:

1. Do not disclose publicly until fixed
2. Email security@aog.dev with details
3. Include reproduction steps if possible
4. We will coordinate disclosure and patching

## Acknowledgments

We follow responsible disclosure practices and appreciate the security community's help in keeping AOG secure.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.