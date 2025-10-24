# 🚀 Quick Reference Cheat Sheet - Day of Interview

## 📋 Pre-Demo Checklist (5 minutes before)

```bash
# Start Redis
brew services start redis
# or
docker run -d -p 6379:6379 --name redis redis:latest

# Test Redis
redis-cli ping  # Should return PONG

# Optional: Start Ollama for AI demo
docker start ollama

# Install dependencies
cd player-service-app
pip install -r requirements.txt

# Test the app
python3 app.py
# Visit http://localhost:8000/health
```

---

## 🎤 Opening Statement (First 30 seconds)

> "Hi everyone! I'm excited to walk through this player service enhancement. This is a Flask-based microservices architecture serving baseball player data. Today I'll demonstrate security fixes, JWT authentication, and Redis caching - features critical for production systems at scale."

---

## 💬 Key Phrases to Use

### When fixing SQL injection:
> "I noticed a SQL injection vulnerability where string formatting could allow an attacker to inject malicious SQL. I'm switching to parameterized queries where the database driver handles escaping."

### When adding authentication:
> "I'm implementing JWT for stateless authentication - perfect for horizontally scaled microservices. The token includes user claims, eliminating database lookups on every request."

### When adding AI feature:
> "I'm implementing an AI-powered query interface using LLM tool calling. Instead of letting the LLM generate SQL directly—which would be a security nightmare—I define safe functions it can call. The LLM acts as intent recognition, translating natural language to validated function calls. This is the same pattern used by ChatGPT plugins."

### When discussing trade-offs:
> "In production, we'd need to consider [X]. The trade-off here is [Y] vs [Z]. For Intuit's scale, I'd recommend [solution] because..."

---

## 🐛 Common Questions & Answers

### Q: "Why JWT over sessions?"
**A:** Stateless, scales horizontally, no session store needed, works great with microservices. Trade-off: can't revoke tokens before expiration unless we maintain a blacklist.

### Q: "What if Redis goes down?"
**A:** (If asked about caching) I'd implement cache-aside pattern with Redis for hot data. For reliability, use Redis Cluster with circuit breaker fallback to database.

### Q: "How do you secure AI queries?"
**A:** LLM never generates raw SQL - it only calls predefined functions with validated parameters. All database queries use parameterized statements. I also log all AI interactions for audit and monitor for prompt injection attempts.

### Q: "How do you handle transactions across services?"
**A:** Saga pattern with compensating transactions, or event sourcing. Can't use ACID transactions across service boundaries.

### Q: "Security concerns?"
**A:** Fixed SQL injection, added JWT auth, input validation, rate limiting, HTTPS only, security headers, secrets in env vars (AWS Secrets Manager in prod).

### Q: "How would you test this?"
**A:** Unit tests (mock database), integration tests (test endpoints with test DB), E2E tests (full flow), load tests, security tests (OWASP ZAP).

### Q: "Monitoring strategy?"
**A:** RED metrics (Rate, Errors, Duration), structured logging with trace IDs, Prometheus + Grafana, distributed tracing with Jaeger, alerting via PagerDuty.

---

## 🧪 Quick Test Commands

```bash
# Get token
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@intuit.com", "password": "admin123"}'

# Use token (replace TOKEN)
curl http://localhost:8000/v1/players \
  -H "Authorization: Bearer TOKEN"

# Test RBAC - should fail with 403
curl http://localhost:8000/v1/admin/stats \
  -H "Authorization: Bearer USER_TOKEN"

# Test RBAC - should succeed
curl http://localhost:8000/v1/admin/stats \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Check cache stats
curl http://localhost:8000/v1/admin/cache/stats \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Test API key (service-to-service)
curl http://localhost:8000/v1/internal/players/player123 \
  -H "X-API-Key: ml-service-key-123"
```

---

## 🔑 Key Technical Terms to Use

- **Stateless authentication**
- **RBAC (Role-Based Access Control)**
- **Cache-aside pattern**
- **Parameterized queries**
- **Horizontal scaling**
- **Circuit breaker**
- **Eventual consistency**
- **Saga pattern**
- **Defense in depth**
- **RED metrics** (Rate, Errors, Duration)
- **Distributed tracing**
- **Service mesh**
- **API Gateway pattern**
- **Connection pooling**
- **Cache invalidation**

---

## 🎯 Demo Timeline

| Time | What | Say |
|------|------|-----|
| 0-5 | Intro | "This is a microservices architecture with player service and ML service..." |
| 5-15 | Fix SQL injection | "Critical security vulnerability using string formatting..." |
| 15-35 | Add JWT auth | "Implementing stateless authentication with RBAC..." |
| 35-60 | Add AI Query | "AI-powered queries using LLM tool calling pattern..." ⭐ |
| 60-75 | Test & discuss | "Let me demonstrate natural language queries..." |

---

## 💎 Production Considerations to Mention

1. **Environment Variables:** "JWT secret should be in AWS Secrets Manager, not env vars"
2. **Password Hashing:** "I'm using plaintext for demo, but production needs bcrypt"
3. **HTTPS:** "Enforce TLS 1.3 only"
4. **Rate Limiting:** "Implement at API Gateway level"
5. **Connection Pooling:** "SQLAlchemy provides this, critical for performance"
6. **Database Indexes:** "Index on playerId and frequently queried columns"
7. **Read Replicas:** "Route reads to replicas to scale"
8. **Monitoring:** "Prometheus metrics, structured logs, distributed tracing"
9. **Circuit Breaker:** "Prevent cascading failures when dependencies fail"
10. **Multi-Region:** "For DR and low latency worldwide"

---

## 🚨 If Something Breaks

### Import Error
```python
# Check dependencies installed
pip install -r requirements.txt
```

### Redis Connection Error
```python
# Check Redis running
redis-cli ping

# If not installed
brew install redis
brew services start redis
```

### Database Error
```python
# Delete and recreate
rm player.db
python3 app.py  # Will recreate from CSV
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in app.py
app.run(host='0.0.0.0', port=8001, debug=True)
```

---

## 🎓 Intuit-Specific Talking Points

- **QuickBooks:** "For multi-tenant SaaS like QuickBooks, row-level security is critical"
- **TurboTax:** "Tax data requires encryption at rest, RBAC, audit logging"
- **Payment Processing:** "PCI DSS compliance, no sensitive data in logs"
- **Scale:** "Intuit handles millions of users during tax season - horizontal scaling essential"
- **Compliance:** "SOC 2, GDPR, data retention policies"

---

## 🌟 Confidence Boosters

- **You know this material** - you just organized it
- **Think aloud** - they want to hear your process
- **Ask questions** - shows critical thinking
- **It's OK to say "I'd look that up"** - nobody knows everything
- **Production awareness** - always mention "in production, we'd..."

---

## 📝 Body Language & Communication

- ✅ **Speak confidently** - "I would do X because..."
- ✅ **Make eye contact** - engage with interviewers
- ✅ **Use whiteboard** - draw architecture diagrams
- ✅ **Ask for feedback** - "Does this approach make sense?"
- ✅ **Manage time** - keep an eye on clock
- ❌ **Don't apologize** - for demo code quality
- ❌ **Don't rush** - better to do less well than more poorly
- ❌ **Don't be defensive** - when they suggest alternatives

---

## 🎯 What Success Looks Like

1. ✅ Fixed critical security issues
2. ✅ Implemented working authentication
3. ✅ Demonstrated scalability thinking
4. ✅ Showed production awareness
5. ✅ Communicated clearly
6. ✅ Handled questions well

**You don't need perfect code. You need to show senior-level thinking.**

---

## 🚀 Final Reminders

- **Water nearby** - stay hydrated
- **Close Slack/email** - minimize distractions
- **Large font** - terminal should be readable
- **Test beforehand** - run through once
- **Backup plan** - have code in GitHub if demo fails
- **Breathe** - you've got this!

---

## 📞 Emergency Fallback

If live coding fails catastrophically:

> "I'm hitting a configuration issue. Rather than burn time debugging, let me walk through the architecture and code I prepared. [Show the code files and explain the design decisions]"

Then pivot to whiteboarding the architecture and discussing design choices.

---

## 🎉 You're Ready!

**Remember:** This is a conversation with colleagues, not an interrogation. They want you to succeed. Show them you think about production systems, security, scalability, and maintainability.

**Now go crush it! 💪**

