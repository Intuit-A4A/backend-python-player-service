# ⚡ Quick Feature Implementation Guide (10-15 min each)

## 🎯 Overview

These are **simplified, interview-friendly implementations** for common follow-up requests. Each can be implemented in 10-15 minutes.

---

## 🤖 Feature 1: Integrate KNN Model with AI Chat (10 minutes)

### **Scenario:**
> "Can you integrate the ML recommendation service with your AI chat feature to help users find players?"

### **What They Want to See:**
- Service-to-service communication
- Error handling for external API calls
- Combining AI with ML recommendations

### **Simple Implementation:**

```python
# ai_query_service.py - Add this method to AIQueryService class

import requests

def _get_similar_players_from_ml(self, player_id: str, count: int = 5) -> List[str]:
    """
    Call the ML service to get similar players
    
    This demonstrates:
    - Service-to-service communication
    - Error handling for external APIs
    - Timeout handling
    - Fallback mechanisms
    """
    try:
        # Call ML service (runs on port 8657)
        response = requests.post(
            'http://localhost:8657/team/generate',
            json={
                'seed_id': player_id,
                'team_size': count
            },
            timeout=3.0  # 3 second timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('member_ids', [])
        else:
            logger.warning(f"ML service returned {response.status_code}")
            return []
            
    except requests.Timeout:
        logger.error("ML service timeout")
        return []  # Graceful degradation
    except Exception as e:
        logger.error(f"ML service error: {e}")
        return []

# Add new function to the tools list
def __init__(self):
    self.player_service = PlayerService()
    
    # Add to existing tools
    self.tools.append({
        "name": "get_similar_players",
        "description": "Find players similar to a given player using ML",
        "parameters": {
            "type": "object",
            "properties": {
                "player_id": {
                    "type": "string",
                    "description": "The player ID to find similar players for"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of similar players to return",
                    "default": 5
                }
            },
            "required": ["player_id"]
        }
    })

# Add execution in _execute_function
def _execute_function(self, function_call: Dict, trace_id: str) -> any:
    # ... existing code ...
    
    elif function_name == 'get_similar_players':
        player_id = parameters.get('player_id')
        count = min(parameters.get('count', 5), 20)  # Cap at 20
        
        # Call ML service
        similar_ids = self._get_similar_players_from_ml(player_id, count)
        
        if not similar_ids:
            return {
                'error': 'ML service unavailable',
                'fallback': 'Try specific player search instead'
            }
        
        # Get details for similar players
        players = []
        for pid in similar_ids:
            player = self.player_service.search_by_player(pid)
            if player:
                players.append(player)
        
        logger.info(f"[{trace_id}] Found {len(players)} similar players via ML")
        return players
```

### **Demo Script:**

**User asks:** "Find me players similar to Babe Ruth"

**Flow:**
1. LLM extracts: `{"name": "get_similar_players", "parameters": {"player_id": "ruthba01"}}`
2. System calls ML service: `POST localhost:8657/team/generate`
3. ML service returns: `["player1", "player2", ...]`
4. System fetches player details from database
5. LLM formats: "Here are 5 players similar to Babe Ruth..."

### **Talking Points:**

> "I've integrated the ML recommendation service with the AI chat. When users ask for similar players, the LLM calls the ML service via HTTP. I've added proper error handling - if the ML service times out or fails, we return an empty list rather than crashing. The timeout is set to 3 seconds to prevent slow responses.
>
> In production, I'd add:
> - Circuit breaker to prevent cascading failures
> - Retry logic with exponential backoff
> - Caching popular recommendations in Redis
> - Health checks to detect if ML service is down
> - Fallback to database similarity (same team, similar height) if ML fails"

---

## 📊 Feature 2: Add Filtering & Sorting to Pagination (10 minutes)

### **Scenario:**
> "Can you add the ability to filter and sort players in your pagination endpoint?"

### **What They Want to See:**
- Dynamic query building
- SQL injection prevention with filters
- Input validation
- Performance considerations

### **Simple Implementation:**

```python
# player_service.py - Add this method

def get_players_filtered(
    self, 
    limit: int = 100,
    offset: int = 0,
    country: Optional[str] = None,
    min_height: Optional[int] = None,
    max_height: Optional[int] = None,
    sort_by: str = 'playerId',
    sort_order: str = 'ASC'
) -> List[Dict]:
    """
    Get players with filtering and sorting
    
    Args:
        limit: Max players to return
        offset: Number to skip
        country: Filter by birth country
        min_height: Minimum height in cm
        max_height: Maximum height in cm
        sort_by: Column to sort by (playerId, height, weight, birthYear)
        sort_order: ASC or DESC
        
    Returns:
        List of player dictionaries
    """
    try:
        # Validate inputs
        limit = min(max(1, limit), 1000)
        offset = max(0, offset)
        
        # Whitelist allowed sort columns (SQL injection prevention!)
        allowed_sort_columns = ['playerId', 'nameFirst', 'nameLast', 
                                'birthYear', 'height', 'weight', 'birthCountry']
        if sort_by not in allowed_sort_columns:
            sort_by = 'playerId'
        
        # Whitelist sort order
        sort_order = 'ASC' if sort_order.upper() == 'ASC' else 'DESC'
        
        # Build WHERE clause with filters
        filters = []
        params = []
        
        if country:
            filters.append("birthCountry = ?")
            params.append(country)
        
        if min_height is not None:
            filters.append("height >= ?")
            params.append(min_height)
        
        if max_height is not None:
            filters.append("height <= ?")
            params.append(max_height)
        
        # Build query
        query = "SELECT * FROM players"
        
        if filters:
            query += " WHERE " + " AND ".join(filters)
        
        # Add ORDER BY (safe - we whitelisted the column!)
        query += f" ORDER BY {sort_by} {sort_order}"
        
        # Add pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute with parameterized query (SQL injection safe!)
        result = self.cursor.execute(query, tuple(params)).fetchall()
        
        players = [self.convert_row_to_dict(row) for row in result]
        
        logger.info(
            f"Retrieved {len(players)} players "
            f"(filters: {len(filters)}, sort: {sort_by} {sort_order})"
        )
        
        return players
        
    except Exception as e:
        logger.error(f"Error in filtered query: {e}")
        raise PlayerServiceException(f"Failed to fetch players: {e}")
```

```python
# app.py - Update the endpoint

@app.route('/v1/players', methods=['GET'])
@require_auth()
@monitor_performance
def get_players():
    """
    Get players with filtering, sorting, and pagination
    
    Query params:
        - limit: Number to return (default 100, max 1000)
        - offset: Number to skip (default 0)
        - country: Filter by birth country (e.g., 'USA', 'DOM')
        - min_height: Minimum height in cm
        - max_height: Maximum height in cm
        - sort_by: Column to sort by (default 'playerId')
        - sort_order: ASC or DESC (default 'ASC')
    
    Examples:
        /v1/players?country=USA&min_height=180&sort_by=height&sort_order=DESC
        /v1/players?sort_by=birthYear&sort_order=ASC&limit=50
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        country = request.args.get('country', type=str)
        min_height = request.args.get('min_height', type=int)
        max_height = request.args.get('max_height', type=int)
        sort_by = request.args.get('sort_by', 'playerId', type=str)
        sort_order = request.args.get('sort_order', 'ASC', type=str)
        
        player_service = PlayerService()
        result = player_service.get_players_filtered(
            limit=limit,
            offset=offset,
            country=country,
            min_height=min_height,
            max_height=max_height,
            sort_by=sort_by,
            sort_order=sort_order
        )
        player_service.close()
        
        logger.info(
            f"[{g.trace_id}] User {g.current_user.get('email')} "
            f"fetched {len(result)} players with filters"
        )
        
        return jsonify({
            'data': result,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(result)
            },
            'filters': {
                'country': country,
                'min_height': min_height,
                'max_height': max_height,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[{g.trace_id}] Error in get_players: {e}")
        return jsonify({
            'error': {
                'code': 'FETCH_ERROR',
                'message': 'Failed to fetch players',
                'trace_id': g.trace_id
            }
        }), 500
```

### **Demo Commands:**

```bash
# Filter by country
curl "http://localhost:8000/v1/players?country=USA" \
  -H "Authorization: Bearer $TOKEN"

# Filter by height range
curl "http://localhost:8000/v1/players?min_height=180&max_height=190" \
  -H "Authorization: Bearer $TOKEN"

# Sort by height descending
curl "http://localhost:8000/v1/players?sort_by=height&sort_order=DESC&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Complex: USA players over 180cm, sorted by birth year
curl "http://localhost:8000/v1/players?country=USA&min_height=180&sort_by=birthYear&sort_order=ASC" \
  -H "Authorization: Bearer $TOKEN"
```

### **Talking Points:**

> "I've added filtering and sorting to the pagination endpoint. Key security consideration: I whitelist the allowed sort columns to prevent SQL injection. Even though users can specify the sort column, it's validated against a whitelist before being used in the query. All filter values use parameterized queries.
>
> For performance, I'd add:
> - Database indexes on commonly filtered columns (birthCountry, height)
> - Validation that combined filters don't return too many results
> - Consider denormalization if complex joins are needed
>
> In production with millions of players:
> - Use Elasticsearch for complex text search and filtering
> - Cache common filter combinations in Redis
> - Add query cost estimation to reject expensive queries
> - Consider using GraphQL for more flexible filtering"

---

## ⏰ Revised 75-Minute Timeline

### **Option A: Core Features Only (Safer)**
| Time | Phase | Features |
|------|-------|----------|
| 0-5 | Intro | Overview |
| 5-15 | Phase 1 | Fix SQL injection |
| 15-35 | Phase 2 | JWT Auth + RBAC |
| 35-55 | Phase 3 | AI Query Service (simplified) |
| 55-65 | Phase 4 | Unit Test + Monitoring (show, don't implement) |
| 65-75 | Phase 5 | Demo & Discussion |

### **Option B: With One Additional Feature (If Ahead)**
| Time | Phase | Features |
|------|-------|----------|
| 0-5 | Intro | Overview |
| 5-13 | Phase 1 | Fix SQL injection (faster) |
| 13-30 | Phase 2 | JWT Auth + RBAC (faster) |
| 30-50 | Phase 3 | AI Query Service |
| 50-60 | **Phase 4** | **Quick feature: KNN integration OR filtering** |
| 60-68 | Phase 5 | Unit Test + Monitoring (show) |
| 68-75 | Phase 6 | Demo everything |

---

## 📝 Simplified Core Implementations

### **Simplified AI Query Service (25 minutes instead of 35)**

**Cut these for time:**
- ❌ Skip the `_format_answer` step (just return raw results)
- ❌ Skip multiple tool definitions (just keep `search_players`)
- ❌ Skip detailed prompt engineering examples

**Keep these:**
- ✅ Basic LLM function calling
- ✅ SQL injection prevention
- ✅ Error handling
- ✅ One working query type

**Minimal Implementation:**

```python
# ai_query_service.py - SIMPLIFIED VERSION

import ollama
import json
import logging
from player_service import PlayerService
import re

logger = logging.getLogger(__name__)

class AIQueryService:
    def __init__(self):
        self.player_service = PlayerService()
    
    def query(self, user_question: str, trace_id: str = "unknown") -> dict:
        """Simple AI query - just extract search parameters"""
        try:
            # Simple prompt
            prompt = f"""Extract search parameters from this question: "{user_question}"
            
Return JSON only:
{{"country": "USA"}} or {{"min_height": 180}} or {{"player_name": "Ruth"}}

Question: {user_question}
JSON:"""
            
            # Call LLM
            response = ollama.chat(
                model='tinyllama',
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            # Extract JSON
            content = response['message']['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                params = json.loads(json_match.group())
                
                # Execute search
                if 'country' in params:
                    results = self._search_by_country(params['country'])
                elif 'min_height' in params:
                    results = self._search_by_height(params['min_height'])
                else:
                    results = []
                
                return {
                    'answer': f"Found {len(results)} players",
                    'results': results[:5],  # First 5 only
                    'count': len(results)
                }
            
            return {'answer': 'Could not understand question', 'results': []}
            
        except Exception as e:
            logger.error(f"AI query error: {e}")
            return {'answer': 'Error processing query', 'error': str(e)}
    
    def _search_by_country(self, country: str) -> list:
        """Parameterized query for country"""
        query = "SELECT * FROM players WHERE birthCountry = ? LIMIT 100"
        result = self.player_service.cursor.execute(query, (country,)).fetchall()
        return [self.player_service.convert_row_to_dict(row) for row in result]
    
    def _search_by_height(self, min_height: int) -> list:
        """Parameterized query for height"""
        query = "SELECT * FROM players WHERE height >= ? LIMIT 100"
        result = self.player_service.cursor.execute(query, (min_height,)).fetchall()
        return [self.player_service.convert_row_to_dict(row) for row in result]
```

**Time saved: 10-15 minutes**

---

### **Simplified Auth (15 minutes instead of 20)**

**Cut these:**
- ❌ API key authentication (keep only JWT)
- ❌ Multiple admin endpoints (just one)
- ❌ Complex error handling

**Keep these:**
- ✅ JWT generation and validation
- ✅ Login endpoint
- ✅ Protected endpoint decorator
- ✅ Basic RBAC (admin vs user)

**Minimal Implementation:**

```python
# auth.py - SIMPLIFIED

import jwt
import datetime
from functools import wraps
from flask import request, jsonify, g

JWT_SECRET = 'demo-secret'  # In production: environment variable

USERS = {
    'admin@intuit.com': {'password': 'admin123', 'roles': ['admin']},
    'user@intuit.com': {'password': 'user123', 'roles': ['user']}
}

def generate_token(email: str, roles: list) -> str:
    """Generate JWT token"""
    payload = {
        'email': email,
        'roles': roles,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token: str) -> dict:
    """Verify JWT token"""
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])

def require_auth(required_roles=None):
    """Decorator for protected routes"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing token'}), 401
            
            token = auth_header.split(' ')[1]
            
            try:
                payload = verify_token(token)
                g.current_user = payload
                
                # Check roles
                if required_roles:
                    if not any(r in payload.get('roles', []) for r in required_roles):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            except:
                return jsonify({'error': 'Invalid token'}), 401
        
        return decorated
    return decorator

def authenticate(email: str, password: str) -> dict:
    """Authenticate user"""
    user = USERS.get(email)
    if user and user['password'] == password:
        return user
    return None
```

**Time saved: 5 minutes**

---

## 🎯 Interview Strategy

### **If Running Behind (Most Likely):**

1. **Prioritize Security + Auth + Basic AI**
   - These are the core requirements
   - Skip advanced features
   
2. **Show, Don't Implement** for:
   - Unit tests (open file, explain, don't write from scratch)
   - Monitoring (show monitoring.py, explain concepts)
   - Additional features (mention in discussion)

3. **Have Code Ready to Paste:**
   - Don't type everything from scratch
   - Have implementations in a scratch file to copy

### **If Running Ahead (Unlikely but Possible):**

1. **Add One Quick Feature:**
   - KNN integration (10 min) - more impressive
   - OR filtering/sorting (10 min) - more practical

2. **Enhance What You Have:**
   - Add one more unit test
   - Show monitoring in action
   - Demo a complex AI query

### **Key Phrases to Save Time:**

Instead of implementing everything, **say:**

> "In production, I'd add [feature X]. The implementation would be [brief explanation]. Given time constraints, I'll focus on the core functionality, but I'm happy to discuss any of these in detail."

---

## 📋 Copy-Paste Ready Code Snippets

### **Quick KNN Integration (paste into ai_query_service.py):**

```python
def _call_ml_service(self, player_id: str, count: int = 5) -> list:
    try:
        r = requests.post('http://localhost:8657/team/generate',
                         json={'seed_id': player_id, 'team_size': count},
                         timeout=3.0)
        return r.json().get('member_ids', []) if r.status_code == 200 else []
    except:
        return []
```

### **Quick Filtering (paste into player_service.py):**

```python
def filter_players(self, country=None, min_height=None, sort_by='playerId'):
    filters, params = [], []
    if country:
        filters.append("birthCountry = ?")
        params.append(country)
    if min_height:
        filters.append("height >= ?")
        params.append(min_height)
    
    query = "SELECT * FROM players"
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += f" ORDER BY {sort_by} LIMIT 100"  # sort_by validated!
    
    result = self.cursor.execute(query, tuple(params)).fetchall()
    return [self.convert_row_to_dict(r) for r in result]
```

---

## ✅ What to Emphasize

**When showing these features, emphasize:**

### **For KNN Integration:**
- ✅ "Service-to-service communication with timeout"
- ✅ "Graceful degradation if ML service fails"
- ✅ "In production: circuit breaker, retry logic, caching"

### **For Filtering/Sorting:**
- ✅ "Whitelist for sort columns prevents SQL injection"
- ✅ "All filters use parameterized queries"
- ✅ "In production: Elasticsearch for complex search, indexes on filtered columns"

### **For Simplified Implementations:**
- ✅ "This is MVP functionality - demonstrates concepts"
- ✅ "Production would add: [X, Y, Z]"
- ✅ "Given time constraints, focused on core functionality"

---

## 🎤 If They Ask to Add Features

**They say:** "Can you add filtering to your pagination?"

**You say:**
> "Absolutely. I'll add query parameter support for common filters like country and height, validate inputs, and use parameterized queries for security. The key security consideration is whitelisting sort columns to prevent SQL injection. Let me implement that..."

*Then paste the simplified filtering code (3 minutes)*

**They say:** "Can you integrate with the ML service?"

**You say:**
> "Great idea! I'll add a function that calls the ML service via HTTP, with proper timeout and error handling. If the ML service fails, we'll gracefully degrade to an empty result. Let me add that to the AI service..."

*Then paste the simplified KNN integration (3 minutes)*

---

## ⏱️ Time Management Tips

1. **Set a timer on your phone** - check after each phase
2. **If behind at 40 minutes**, skip to simplified versions
3. **If ahead at 50 minutes**, add a quick feature
4. **Save 10 minutes for demo** - don't code until 65 minutes

---

## 🎉 You're Ready for Anything!

With these simplified implementations, you can:
- ✅ Complete core features in time
- ✅ Add extras if ahead of schedule
- ✅ Handle follow-up feature requests
- ✅ Stay calm if running behind

**Remember:** Quality over quantity. Better to have 3 features working well than 5 features half-done!

Good luck! 🚀

