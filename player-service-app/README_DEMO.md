# 🚀 Intuit Interview Demo - Quick Start Guide

## 🎯 What This Is

This is your **75-minute live coding demo** for the Intuit Senior Backend Engineer interview. Everything you need is prepared and ready to go.

---

## 📚 Documentation Files (Read in Order)

1. **../INTERVIEW_SUMMARY.md** ⭐ START HERE
   - Complete overview and 3-day study plan
   - Read this first to understand everything

2. **../INTERVIEW_PREP_GUIDE.md** 📖 Study Material
   - Deep dive into 13 backend concepts
   - Interview questions and answers
   - Read 1-2 days before interview

3. **../DEMO_IMPLEMENTATION.md** 💻 Implementation Guide
   - Step-by-step code for the demo
   - Use during live coding
   - Copy-paste ready code

4. **../CHEAT_SHEET.md** ⚡ Day-Of Reference
   - Quick reference for interview day
   - Have this open during demo
   - 5-minute review before interview

---

## ⚡ Quick Setup (5 Minutes)

```bash
# 1. Navigate to player-service-app
cd player-service-app

# 2. Run automated setup
./setup_demo.sh

# 3. Start the application
python3 app.py

# 4. Test it works
curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "timestamp": 1729684200.0
}
```

---

## 🧪 Test the Demo (Before Interview)

### **Option 1: Use Postman (Recommended)**

1. Import `Postman_Collection.json` into Postman
2. Run requests in order:
   - Health Check
   - Login - Admin (token auto-saved)
   - Get All Players (uses saved token)
   - Try admin endpoints with user vs admin token

### **Option 2: Use curl**

```bash
# 1. Login as admin
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@intuit.com", "password": "admin123"}'

# Save the token from response
TOKEN="eyJ..."

# 2. Get players with authentication
curl http://localhost:8000/v1/players \
  -H "Authorization: Bearer $TOKEN"

# 3. Test RBAC - access admin endpoint
curl http://localhost:8000/v1/admin/stats \
  -H "Authorization: Bearer $TOKEN"

# 4. Check cache stats
curl http://localhost:8000/v1/admin/cache/stats \
  -H "Authorization: Bearer $TOKEN"
```

### **Option 3: Run Tests**

```bash
# Run all tests
pytest test_demo.py -v

# Run specific test
pytest test_demo.py::test_login_success -v
```

---

## 🎬 Demo Day Timeline

### **Before Interview (5-10 minutes):**

```bash
# 1. Start Redis
brew services start redis
# or
docker run -d -p 6379:6379 --name redis redis:latest

# 2. Test Redis
redis-cli ping  # Should return PONG

# 3. Navigate to app directory
cd player-service-app

# 4. Activate virtual environment
source env/bin/activate

# 5. Start app
python3 app.py

# 6. Test in another terminal
curl http://localhost:8000/health

# 7. Open CHEAT_SHEET.md on second monitor

# 8. Close distracting apps

# 9. Increase terminal font size

# 10. Deep breath - you're ready!
```

---

### **During Interview (75 minutes):**

**Follow DEMO_IMPLEMENTATION.md exactly:**

| Time | Phase | What to Do |
|------|-------|------------|
| 0-5 min | Introduction | Use opening script from CHEAT_SHEET.md |
| 5-20 min | Security Fixes | Fix SQL injection in player_service.py |
| 20-50 min | Authentication | Add JWT auth, RBAC, login endpoint |
| 50-65 min | Caching | Add Redis caching layer |
| 65-75 min | Testing & Discussion | Demo features, discuss production |

**Key: Think aloud the entire time!**

---

## 🎤 Opening Statement (Memorize This)

> "Hi everyone! I'm excited to walk through enhancements I've made to this player service.
> 
> **Current State:** This is a Flask-based microservices architecture with two services - Player Service handles CRUD operations, and ML Service provides team recommendations using a KNN model.
> 
> **What I'll demonstrate today:**
> 1. First, I noticed critical security vulnerabilities - SQL injection risks - so I'll address those
> 2. Then implement JWT-based authentication with role-based access control
> 3. Finally, add a Redis caching layer for performance optimization
> 
> **My assumptions:**
> - This will run in a production environment with multiple instances
> - We need horizontal scalability
> - Security is critical given Intuit handles financial data
> - We expect high read traffic
> 
> Let's start with the security fixes..."

---

## 🔑 Test Credentials

### **Users:**
- **Admin:** admin@intuit.com / admin123
- **User:** user@intuit.com / user123

### **API Keys (Service-to-Service):**
- **ML Service:** ml-service-key-123

---

## 📊 What You're Demonstrating

### **1. Security Mindset** ✅
- SQL injection fix
- Input validation
- JWT authentication
- Security headers

### **2. Scalability** ✅
- Stateless auth (JWT)
- Caching layer (Redis)
- Pagination
- Connection pooling awareness

### **3. Production Readiness** ✅
- Structured logging
- Trace IDs
- Error handling
- Health checks

### **4. Code Quality** ✅
- Type hints
- Documentation
- Testing
- Clean architecture

### **5. Architectural Thinking** ✅
- Microservices patterns
- RBAC implementation
- Cache-aside pattern
- API design best practices

---

## 🧠 Quick Concept Reference

### **JWT Authentication:**
- **What:** JSON Web Token for stateless auth
- **Why:** Scales horizontally, no session storage
- **Trade-off:** Can't revoke before expiration

### **RBAC:**
- **What:** Role-Based Access Control
- **Why:** Different permissions for different users
- **Example:** Admin can access /admin/stats, users cannot

### **Cache-Aside Pattern:**
```
1. Check cache
2. If miss → fetch from DB
3. Store in cache
4. Return data
```

### **SQL Injection:**
```python
# VULNERABLE
query = f"SELECT * FROM players WHERE id='{user_id}'"

# SECURE
query = "SELECT * FROM players WHERE id=?"
cursor.execute(query, (user_id,))
```

---

## 💬 Common Questions & Quick Answers

### **Q: Why JWT over sessions?**
**A:** Stateless, scales horizontally, works great with microservices. Trade-off: can't revoke tokens easily.

### **Q: What if Redis goes down?**
**A:** Circuit breaker pattern + fallback to database. Use Redis Cluster with replication in production.

### **Q: How do you test this?**
**A:** Unit tests (mock DB), integration tests (test endpoints), E2E tests, load tests.

### **Q: How would you deploy this?**
**A:** Docker + Kubernetes with 3 replicas, Redis StatefulSet, ALB for load balancing, EKS on AWS.

### **Q: Security concerns?**
**A:** Fixed SQL injection, JWT auth, input validation, rate limiting, HTTPS only, secrets in AWS Secrets Manager.

---

## 🚨 Emergency Troubleshooting

### **Redis Connection Error:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis
# or
docker run -d -p 6379:6379 --name redis redis:latest
```

### **Import Error:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### **Database Error:**
```bash
# Delete and recreate
rm player.db
python3 app.py
```

### **Port Already in Use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### **Complete Environment Reset:**
```bash
./setup_demo.sh
```

---

## 🎯 Success Criteria

After the demo, you should have demonstrated:

- ✅ Fixed critical security vulnerability
- ✅ Implemented working authentication
- ✅ Added performance optimization
- ✅ Discussed production considerations
- ✅ Communicated clearly
- ✅ Handled questions confidently

**Remember: It's not about perfect code, it's about demonstrating senior-level thinking.**

---

## 📁 File Structure

```
player-service-app/
├── app.py                      # Main Flask app (you'll modify this)
├── player_service.py           # Database layer (fix SQL injection here)
├── auth.py                     # Authentication module (you'll create this)
├── cache.py                    # Caching module (you'll create this)
├── test_demo.py                # Integration tests (you'll create this)
├── requirements.txt            # Dependencies
├── Player.csv                  # Data source
├── setup_demo.sh              # Automated setup script
├── Postman_Collection.json    # API testing collection
└── README_DEMO.md             # This file
```

---

## 🌟 Confidence Boosters

Before you start, remember:

- ✅ You've prepared more than most candidates
- ✅ You understand the concepts deeply
- ✅ You have working code ready
- ✅ You've practiced the demo
- ✅ You know how to discuss production systems
- ✅ They want you to succeed

**You've got this! 🚀**

---

## 📞 Final Checklist

Print this and check off before starting:

### **Technical:**
- [ ] Redis running
- [ ] Python app running
- [ ] Health endpoint works
- [ ] Postman collection imported or curl commands ready
- [ ] Terminal font size increased
- [ ] CHEAT_SHEET.md open on second monitor

### **Environment:**
- [ ] Quiet room
- [ ] Good lighting
- [ ] Stable internet
- [ ] Camera/mic tested
- [ ] Notifications off
- [ ] Water nearby
- [ ] Bathroom break taken

### **Mental:**
- [ ] Reviewed CHEAT_SHEET.md
- [ ] Practiced opening statement
- [ ] Deep breathing
- [ ] Confident mindset

---

## 🎉 Ready to Go!

**Now close this file, take a deep breath, and crush that interview!**

*Good luck! 💪*

