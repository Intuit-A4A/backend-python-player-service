# 🏗️ Architecture Diagrams & Visual Guides

## 📐 System Overview - Before & After

### **Before (Current State):**
```
┌─────────────────────────────────────────────┐
│                  Client                      │
└───────────────┬─────────────────────────────┘
                │ HTTP (No Auth!)
                ▼
┌───────────────────────────────────────────────┐
│          Flask REST API                       │
│  ┌─────────────────────────────────────────┐ │
│  │  /v1/players                             │ │
│  │  /v1/players/<id>  ← SQL INJECTION!     │ │
│  │  /v1/chat                                │ │
│  └─────────────────────────────────────────┘ │
└───────────────┬───────────────────────────────┘
                │
                ▼
┌───────────────────────────────┐
│      SQLite Database          │
│  (No connection pooling)      │
└───────────────────────────────┘

❌ Issues:
- No authentication
- SQL injection vulnerability
- No caching
- No logging
- No error handling
```

### **After (Your Demo):**
```
┌─────────────────────────────────────────────┐
│                  Client                      │
└───────────────┬─────────────────────────────┘
                │ HTTPS + JWT Token
                ▼
┌────────────────────────────────────────────────────────┐
│          Flask REST API (Enhanced)                     │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Middleware Layer                                 │ │
│  │  • Authentication (JWT Verification)              │ │
│  │  • Authorization (RBAC)                           │ │
│  │  • Rate Limiting                                  │ │
│  │  • Request Tracing (Trace ID)                     │ │
│  │  • Security Headers                               │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Endpoints                                        │ │
│  │  • POST /v1/auth/login (Public)                   │ │
│  │  • GET  /v1/auth/me (Protected)                   │ │
│  │  • GET  /v1/players (Protected)                   │ │
│  │  • GET  /v1/players/<id> (Protected + Cached)     │ │
│  │  • GET  /v1/admin/stats (Admin Only)              │ │
│  │  • GET  /v1/admin/cache/stats (Admin Only)        │ │
│  │  • POST /v1/admin/cache/invalidate (Admin Only)   │ │
│  │  • GET  /v1/internal/players/<id> (API Key)       │ │
│  └──────────────────────────────────────────────────┘ │
└────────┬─────────────────────────────┬─────────────────┘
         │                             │
         ▼                             ▼
┌─────────────────────┐    ┌────────────────────────┐
│   Redis Cache       │    │  SQLite Database       │
│  (TTL: 1 hour)      │    │  (Parameterized        │
│                     │    │   Queries)             │
│  • Player data      │    │                        │
│  • TTL management   │    │  • Players table       │
│  • Hit rate: ~80%   │    │  • Indexed columns     │
└─────────────────────┘    └────────────────────────┘

✅ Improvements:
- JWT authentication
- RBAC (admin/user roles)
- Redis caching
- SQL injection fixed
- Structured logging
- Error handling
```

---

## 🔐 Authentication Flow

### **Login Flow:**
```
┌────────┐                                        ┌────────┐
│ Client │                                        │ Server │
└───┬────┘                                        └───┬────┘
    │                                                 │
    │  POST /v1/auth/login                            │
    │  {email, password}                              │
    ├────────────────────────────────────────────────>│
    │                                                 │
    │                                                 │ 1. Validate credentials
    │                                                 │    (check USERS_DB)
    │                                                 │
    │                                                 │ 2. Generate JWT token
    │                                                 │    payload = {
    │                                                 │      user_id,
    │                                                 │      email,
    │                                                 │      roles,
    │                                                 │      exp: 24h
    │                                                 │    }
    │                                                 │
    │  200 OK                                         │
    │  {token, user}                                  │
    │<────────────────────────────────────────────────┤
    │                                                 │
    │  Client stores token                            │
    │  (localStorage or memory)                       │
    │                                                 │
```

### **Protected Request Flow:**
```
┌────────┐                                        ┌────────┐
│ Client │                                        │ Server │
└───┬────┘                                        └───┬────┘
    │                                                 │
    │  GET /v1/players                                │
    │  Authorization: Bearer <JWT>                    │
    ├────────────────────────────────────────────────>│
    │                                                 │
    │                                                 │ 1. Extract token from header
    │                                                 │
    │                                                 │ 2. Verify token signature
    │                                                 │    (using JWT_SECRET)
    │                                                 │
    │                                                 │ 3. Check expiration
    │                                                 │
    │                                                 │ 4. Extract user claims
    │                                                 │    (user_id, roles)
    │                                                 │
    │                                                 │ 5. Check RBAC
    │                                                 │    (if required_roles)
    │                                                 │
    │                                                 │ 6. Execute endpoint logic
    │                                                 │
    │  200 OK                                         │
    │  {data: [...]}                                  │
    │<────────────────────────────────────────────────┤
    │                                                 │
```

---

## 💾 Caching Flow (Cache-Aside Pattern)

### **Read with Cache:**
```
┌────────┐         ┌────────┐         ┌───────┐         ┌──────────┐
│ Client │         │  API   │         │ Redis │         │ Database │
└───┬────┘         └───┬────┘         └───┬───┘         └────┬─────┘
    │                  │                   │                   │
    │ GET /v1/players/123                  │                   │
    ├─────────────────>│                   │                   │
    │                  │                   │                   │
    │                  │ 1. Check cache    │                   │
    │                  │ GET player:123    │                   │
    │                  ├──────────────────>│                   │
    │                  │                   │                   │
    │                  │ Cache MISS        │                   │
    │                  │<──────────────────┤                   │
    │                  │                   │                   │
    │                  │ 2. Query database │                   │
    │                  │ SELECT * FROM players WHERE id=123    │
    │                  ├───────────────────────────────────────>│
    │                  │                   │                   │
    │                  │ Player data       │                   │
    │                  │<───────────────────────────────────────┤
    │                  │                   │                   │
    │                  │ 3. Store in cache │                   │
    │                  │ SET player:123, TTL=3600              │
    │                  ├──────────────────>│                   │
    │                  │                   │                   │
    │                  │ OK                │                   │
    │                  │<──────────────────┤                   │
    │                  │                   │                   │
    │ 4. Return data   │                   │                   │
    │<─────────────────┤                   │                   │
    │                  │                   │                   │
    │                  │                   │                   │
    │ GET /v1/players/123 (2nd request)    │                   │
    ├─────────────────>│                   │                   │
    │                  │                   │                   │
    │                  │ 1. Check cache    │                   │
    │                  │ GET player:123    │                   │
    │                  ├──────────────────>│                   │
    │                  │                   │                   │
    │                  │ Cache HIT! ⚡      │                   │
    │                  │<──────────────────┤                   │
    │                  │                   │                   │
    │ 2. Return cached │                   │                   │
    │<─────────────────┤                   │                   │
    │ (Much faster!)   │                   │                   │
```

**Performance Impact:**
- **Without cache:** ~50-100ms (database query)
- **With cache:** ~1-5ms (Redis lookup)
- **10-50x faster!**

---

## 🏢 Microservices Architecture (Production)

### **Your Demo in Production Context:**

```
                        Internet
                           │
                           ▼
                   ┌───────────────┐
                   │   CloudFlare  │ (DDoS Protection)
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  API Gateway  │ (Kong/AWS API Gateway)
                   │               │
                   │  • Auth       │
                   │  • Rate Limit │
                   │  • Routing    │
                   └───────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Player Service│  │   ML Service  │  │  Auth Service │
│  (Your Demo)  │  │               │  │               │
│               │  │  • Team Rec   │  │  • Okta       │
│  • CRUD       │  │  • KNN Model  │  │  • SSO        │
│  • Caching    │  │               │  │               │
└───────┬───────┘  └───────┬───────┘  └───────────────┘
        │                  │
        │                  │
        └────────┬─────────┘
                 │
                 ▼
        ┌────────────────┐
        │   Event Bus    │ (Kafka/RabbitMQ)
        │                │
        │  Topics:       │
        │  • player.*    │
        │  • team.*      │
        └────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │   Consumers    │
        │                │
        │  • Analytics   │
        │  • Audit Log   │
        │  • Search Idx  │
        └────────────────┘


Data Layer:
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   RDS Multi-AZ │  │ Redis Cluster  │  │   S3 Backups   │
│   (Primary +   │  │  (3 nodes)     │  │                │
│   Replicas)    │  │                │  │                │
└────────────────┘  └────────────────┘  └────────────────┘


Observability:
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   Prometheus   │  │   Jaeger       │  │   ELK Stack    │
│   (Metrics)    │  │   (Tracing)    │  │   (Logs)       │
└────────────────┘  └────────────────┘  └────────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                   ┌───────────────┐
                   │    Grafana    │ (Dashboards)
                   └───────────────┘
```

---

## 🎯 Request Flow with Tracing

### **Distributed Tracing Example:**

```
Client Request: GET /v1/players/123
Trace-ID: abc-123-def

┌─────────────────────────────────────────────────────┐
│ API Gateway                         [abc-123-def]   │
│ ├─ Auth check: 2ms                                  │
│ ├─ Rate limit check: 1ms                            │
│ └─ Route to Player Service                          │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│ Player Service                      [abc-123-def]   │
│ ├─ JWT verification: 3ms                            │
│ ├─ RBAC check: 1ms                                  │
│ ├─ Cache lookup: 2ms (HIT!)                         │
│ └─ Return cached data                               │
│                                                      │
│ Total: 9ms                                          │
└─────────────────────────────────────────────────────┘

Logs (searchable by trace ID):
[2025-10-23T10:30:00] [abc-123-def] API Gateway: Received request
[2025-10-23T10:30:00] [abc-123-def] Player Service: Cache HIT player:123
[2025-10-23T10:30:00] [abc-123-def] Player Service: Response 200 (9ms)

Metrics:
- request_duration{service="player-service", endpoint="/players/123"}: 9ms
- cache_hit_rate{service="player-service"}: 82%
- http_requests_total{service="player-service", status="200"}: +1
```

---

## 🔒 RBAC (Role-Based Access Control)

### **Permission Matrix:**

```
┌──────────────────┬────────┬────────┬──────────┐
│   Endpoint       │  User  │ Admin  │ API Key  │
├──────────────────┼────────┼────────┼──────────┤
│ POST /auth/login │   ✅   │   ✅   │    ❌    │
│ GET  /auth/me    │   ✅   │   ✅   │    ❌    │
├──────────────────┼────────┼────────┼──────────┤
│ GET  /players    │   ✅   │   ✅   │    ❌    │
│ GET  /players/id │   ✅   │   ✅   │    ❌    │
├──────────────────┼────────┼────────┼──────────┤
│ GET  /admin/stats│   ❌   │   ✅   │    ❌    │
│ GET  /admin/cache│   ❌   │   ✅   │    ❌    │
│ POST /admin/cache│   ❌   │   ✅   │    ❌    │
├──────────────────┼────────┼────────┼──────────┤
│ GET  /internal/* │   ❌   │   ❌   │    ✅    │
└──────────────────┴────────┴────────┴──────────┘

Legend:
✅ = Allowed
❌ = Forbidden (401 Unauthorized or 403 Forbidden)
```

### **Decision Flow:**

```
                Request Received
                       │
                       ▼
            ┌──────────────────────┐
            │ Does endpoint need   │
            │   authentication?    │
            └──────┬─────────┬─────┘
                   │         │
              No   │         │  Yes
                   │         │
                   ▼         ▼
            Allow Access   Extract Token/API Key
                              │
                              ▼
                   ┌──────────────────────┐
                   │   Is token valid?    │
                   └──────┬─────────┬─────┘
                          │         │
                     No   │         │  Yes
                          │         │
                          ▼         ▼
                   401 Unauthorized  Extract user/service
                                    identity & roles
                                          │
                                          ▼
                              ┌──────────────────────┐
                              │ Does role match      │
                              │  required_roles?     │
                              └──────┬─────────┬─────┘
                                     │         │
                                No   │         │  Yes
                                     │         │
                                     ▼         ▼
                          403 Forbidden   Allow Access
                                          Execute Endpoint
```

---

## 📊 Database Schema & Indexing

### **Players Table:**

```sql
CREATE TABLE players (
    playerId      TEXT PRIMARY KEY,   -- Index automatically
    nameFirst     TEXT,
    nameLast      TEXT,
    birthYear     INTEGER,
    birthMonth    INTEGER,
    birthDay      INTEGER,
    birthCountry  TEXT,               -- Should index if querying
    birthState    TEXT,
    birthCity     TEXT,
    height        INTEGER,
    weight        INTEGER,
    bats          TEXT,
    throws        TEXT,
    debut         TEXT,
    finalGame     TEXT
);

-- Recommended indexes for performance
CREATE INDEX idx_birth_country ON players(birthCountry);
CREATE INDEX idx_name_last ON players(nameLast);
CREATE INDEX idx_birth_year ON players(birthYear);
```

### **Query Performance:**

```
Without Index (Table Scan):
SELECT * FROM players WHERE birthCountry='USA';
→ Scans ALL rows: O(n) time
→ 100,000 players = 100,000 rows scanned

With Index (Index Scan):
SELECT * FROM players WHERE birthCountry='USA';
→ Uses B-tree index: O(log n) time
→ 100,000 players = ~17 comparisons
→ 5,882x faster!
```

---

## 🎨 Error Response Format

### **Consistent Error Structure:**

```json
{
  "error": {
    "code": "PLAYER_NOT_FOUND",
    "message": "No player found with ID 'xyz123'",
    "status": 404,
    "trace_id": "abc-123-def-456",
    "timestamp": "2025-10-23T10:30:00Z",
    "details": {
      "player_id": "xyz123",
      "suggestion": "Check if player ID is correct"
    }
  }
}
```

### **HTTP Status Code Usage:**

```
200 OK              → Successful GET/PUT/PATCH
201 Created         → Successful POST (resource created)
204 No Content      → Successful DELETE
400 Bad Request     → Invalid input (validation error)
401 Unauthorized    → Missing/invalid authentication
403 Forbidden       → Authenticated but insufficient permissions
404 Not Found       → Resource doesn't exist
429 Too Many Reqs   → Rate limit exceeded
500 Internal Error  → Unexpected server error
503 Service Unavail → Dependency down (DB, cache, etc.)
```

---

## 🔄 Deployment Pipeline

### **CI/CD Flow:**

```
Developer
   │
   │ git push
   ▼
┌──────────────┐
│   GitHub     │
└──────┬───────┘
       │ webhook
       ▼
┌──────────────┐
│  Jenkins /   │
│  GitLab CI   │
└──────┬───────┘
       │
       ├─> 1. Run Tests (pytest)
       │
       ├─> 2. Lint Code (pylint, black)
       │
       ├─> 3. Security Scan (Snyk, Bandit)
       │
       ├─> 4. Build Docker Image
       │
       ├─> 5. Push to ECR
       │
       ├─> 6. Deploy to Dev Environment
       │
       ├─> 7. Run Integration Tests
       │
       ├─> 8. Deploy to Staging (Canary: 10%)
       │
       ├─> 9. Monitor Metrics (5 min)
       │   │
       │   ├─ Error rate OK?
       │   ├─ Latency OK?
       │   └─ Health checks OK?
       │
       ├─> 10. Rollout to Staging (100%)
       │
       ├─> 11. Manual Approval Gate
       │
       └─> 12. Deploy to Production (Canary: 5% → 50% → 100%)
```

---

## 📈 Monitoring Dashboard

### **Key Metrics to Display:**

```
┌─────────────────────────────────────────────────────────┐
│  Player Service Dashboard                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Request Rate (QPS)                                      │
│  ┌────────────────────────────────────┐                 │
│  │ ▁▂▃▄▅▆▇█  150 req/s                │                 │
│  └────────────────────────────────────┘                 │
│                                                          │
│  Error Rate                                              │
│  ┌────────────────────────────────────┐                 │
│  │ ▁▁▁▁▁▁▁▁  0.02% (Target: < 1%)     │  ✅            │
│  └────────────────────────────────────┘                 │
│                                                          │
│  Latency (p99)                                           │
│  ┌────────────────────────────────────┐                 │
│  │ ▁▁▂▂▃▃▄▄  85ms (Target: < 500ms)   │  ✅            │
│  └────────────────────────────────────┘                 │
│                                                          │
│  Cache Hit Rate                                          │
│  ┌────────────────────────────────────┐                 │
│  │ █████████░  82% (Target: > 70%)    │  ✅            │
│  └────────────────────────────────────┘                 │
│                                                          │
│  Database Connections                                    │
│  ┌────────────────────────────────────┐                 │
│  │ ▁▂▃▃▂▁▁▁  8/10 used                │  ✅            │
│  └────────────────────────────────────┘                 │
│                                                          │
│  Top Endpoints (QPS)                                     │
│  • GET  /v1/players     → 95 req/s                      │
│  • GET  /v1/players/id  → 45 req/s                      │
│  • POST /v1/auth/login  → 10 req/s                      │
│                                                          │
│  Recent Errors (Last 5 minutes)                          │
│  • 401 Unauthorized     → 3 occurrences                 │
│  • 404 Not Found        → 12 occurrences                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Use These Diagrams During Interview

**When discussing:**
- **Architecture:** Show "System Overview - Before & After"
- **Authentication:** Show "Login Flow" and "Protected Request Flow"
- **Caching:** Show "Caching Flow"
- **Microservices:** Show "Microservices Architecture"
- **Monitoring:** Show "Request Flow with Tracing"
- **RBAC:** Show "Permission Matrix"

**Pro tip:** Draw these on a whiteboard during discussion to show architectural thinking!

---

## 🚀 You're Ready!

These diagrams help you visualize and explain the system architecture. Use them to guide your discussions during the interview.

**Good luck! 💪**

