# 🚀 Advanced Features for Senior-Level Demo

## Feature 1: Advanced Pagination (Making It Senior-Level)

### ❌ Basic Pagination (Too Simple)
```python
@app.route('/v1/players?limit=10&offset=20')
```

### ✅ Senior-Level Pagination (Impressive)

**What makes it senior-level:**
1. **Cursor-based pagination** (better for large datasets)
2. **Hypermedia links** (HATEOAS - REST maturity level 3)
3. **Performance optimization** discussion
4. **Trade-offs** between offset vs cursor-based

### Implementation:

```python
# player_service.py - Add cursor-based pagination

def get_players_paginated(self, limit: int = 100, cursor: Optional[str] = None) -> Dict:
    """
    Get players with cursor-based pagination
    
    Cursor-based pagination is better than offset for:
    - Large datasets (offset gets slower as you paginate deeper)
    - Real-time data (offset can skip/duplicate if data changes)
    - Database performance (can use index scan vs table scan)
    
    Args:
        limit: Number of players to return
        cursor: Cursor from previous page (base64 encoded last player ID)
        
    Returns:
        Dictionary with players, next_cursor, and metadata
    """
    try:
        limit = min(max(1, limit), 1000)
        
        if cursor:
            # Decode cursor (base64 encoded player ID)
            import base64
            last_player_id = base64.b64decode(cursor).decode('utf-8')
            
            # Query players after cursor
            # This uses index on playerId - very fast!
            query = """
                SELECT * FROM players 
                WHERE playerId > ? 
                ORDER BY playerId ASC 
                LIMIT ?
            """
            result = self.cursor.execute(query, (last_player_id, limit + 1)).fetchall()
        else:
            # First page
            query = "SELECT * FROM players ORDER BY playerId ASC LIMIT ?"
            result = self.cursor.execute(query, (limit + 1,)).fetchall()
        
        # Check if there are more results
        has_next = len(result) > limit
        players_data = result[:limit] if has_next else result
        
        # Convert to dictionaries
        players = [self.convert_row_to_dict(row) for row in players_data]
        
        # Generate next cursor if there are more results
        next_cursor = None
        if has_next and players:
            last_player = players[-1]
            next_cursor = base64.b64encode(
                last_player['playerId'].encode('utf-8')
            ).decode('utf-8')
        
        return {
            'data': players,
            'pagination': {
                'limit': limit,
                'count': len(players),
                'has_next': has_next,
                'next_cursor': next_cursor
            }
        }
        
    except Exception as e:
        logger.error(f"Error in paginated query: {e}")
        raise PlayerServiceException(f"Pagination failed: {e}")
```

### API Endpoint with HATEOAS:

```python
# app.py - Enhanced pagination endpoint

@app.route('/v1/players', methods=['GET'])
@require_auth()
def get_players():
    """
    Get players with cursor-based pagination and HATEOAS links
    
    Query params:
        - limit: Number of players (default 100, max 1000)
        - cursor: Cursor from previous page
        
    Response includes hypermedia links for next/prev pages
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        cursor = request.args.get('cursor', None, type=str)
        
        player_service = PlayerService()
        result = player_service.get_players_paginated(limit=limit, cursor=cursor)
        player_service.close()
        
        # Build HATEOAS links (REST Level 3 - Richardson Maturity Model)
        base_url = request.base_url
        links = {
            'self': f"{base_url}?limit={limit}" + (f"&cursor={cursor}" if cursor else "")
        }
        
        if result['pagination']['has_next']:
            next_cursor = result['pagination']['next_cursor']
            links['next'] = f"{base_url}?limit={limit}&cursor={next_cursor}"
        
        # Add links to response
        response = {
            'data': result['data'],
            'pagination': result['pagination'],
            '_links': links  # HATEOAS
        }
        
        logger.info(
            f"[{g.trace_id}] User {g.current_user.get('email')} "
            f"fetched {len(result['data'])} players "
            f"(cursor={'present' if cursor else 'none'})"
        )
        
        return jsonify(response), 200
        
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

### Interview Talking Points:

**When implementing pagination, say:**

> "I'm implementing cursor-based pagination instead of offset-based. Here's why:
> 
> **Offset-based problems:**
> - Performance degrades as offset increases: `SELECT * FROM players LIMIT 100 OFFSET 10000` - database scans and skips 10,000 rows!
> - Inconsistent results if data changes during pagination (can skip or duplicate items)
> 
> **Cursor-based benefits:**
> - Consistent performance: `SELECT * FROM players WHERE id > 'cursor' LIMIT 100` uses index
> - Stable results even if data changes
> - Used by Facebook, Twitter, Stripe APIs
> 
> **Trade-off:** Can't jump to arbitrary page (no 'page 5'), but for infinite scroll or sequential access, it's much better.
> 
> I'm also implementing **HATEOAS** (Hypermedia As The Engine Of Application State) - the highest level of REST API maturity. The response includes links for navigation, so clients don't need to construct URLs themselves."

**Response example:**
```json
{
  "data": [...],
  "pagination": {
    "limit": 100,
    "count": 100,
    "has_next": true,
    "next_cursor": "cGxheWVyMTIz"
  },
  "_links": {
    "self": "http://localhost:8000/v1/players?limit=100",
    "next": "http://localhost:8000/v1/players?limit=100&cursor=cGxheWVyMTIz"
  }
}
```

---

## Feature 2: AI-Powered Natural Language Player Query (EXCELLENT FOR AI ROUND!)

This is **perfect** for demonstrating AI integration at senior level!

### What This Demonstrates:
1. ✅ **LLM Tool/Function Calling** - Modern AI integration pattern
2. ✅ **Prompt Engineering** - How to guide LLM effectively
3. ✅ **Error Handling** - LLMs are unreliable, need fallbacks
4. ✅ **RAG Pattern** - Retrieval-Augmented Generation
5. ✅ **Security** - SQL injection prevention with LLMs
6. ✅ **Production Readiness** - Validation, logging, monitoring

### Architecture:

```
User Question: "Show me all players from USA who are taller than 6 feet"
                           │
                           ▼
                  ┌─────────────────┐
                  │   LLM Service   │
                  │   (Ollama)      │
                  └────────┬────────┘
                           │
                  Generates function call:
                  {
                    "function": "search_players",
                    "args": {
                      "country": "USA",
                      "min_height": 183
                    }
                  }
                           │
                           ▼
                  ┌─────────────────┐
                  │  Player Service │
                  │  (Execute Query)│
                  └────────┬────────┘
                           │
                  Returns: [Player1, Player2, ...]
                           │
                           ▼
                  ┌─────────────────┐
                  │   LLM Service   │
                  │ (Format Answer) │
                  └────────┬────────┘
                           │
                           ▼
            "I found 45 players from USA taller 
             than 6 feet. Here are the top 5..."
```

### Implementation:

```python
# ai_query_service.py - NEW FILE

import ollama
import json
import logging
from typing import Dict, List, Optional
from player_service import PlayerService
import re

logger = logging.getLogger(__name__)

class AIQueryService:
    """
    AI-powered natural language query service for players
    
    Demonstrates:
    - LLM tool/function calling
    - Prompt engineering
    - Error handling with LLMs
    - Security (preventing SQL injection via LLM)
    - Structured output parsing
    """
    
    def __init__(self):
        self.player_service = PlayerService()
        
        # Define available tools/functions the LLM can call
        self.tools = [
            {
                "name": "search_players",
                "description": "Search for baseball players with filters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "Filter by birth country (e.g., 'USA', 'DOM', 'VEN')"
                        },
                        "min_height": {
                            "type": "integer",
                            "description": "Minimum height in centimeters"
                        },
                        "max_height": {
                            "type": "integer",
                            "description": "Maximum height in centimeters"
                        },
                        "bats": {
                            "type": "string",
                            "enum": ["L", "R", "B"],
                            "description": "Batting hand: L (left), R (right), B (both)"
                        },
                        "throws": {
                            "type": "string",
                            "enum": ["L", "R"],
                            "description": "Throwing hand: L (left), R (right)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    }
                }
            },
            {
                "name": "get_player_by_name",
                "description": "Get specific player by name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "Player's first name"
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Player's last name"
                        }
                    },
                    "required": ["last_name"]
                }
            },
            {
                "name": "get_player_statistics",
                "description": "Get statistics about players",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stat_type": {
                            "type": "string",
                            "enum": ["average_height", "average_weight", "count_by_country"],
                            "description": "Type of statistic to calculate"
                        },
                        "country": {
                            "type": "string",
                            "description": "Filter by country (optional)"
                        }
                    },
                    "required": ["stat_type"]
                }
            }
        ]
    
    def query(self, user_question: str, trace_id: str = "unknown") -> Dict:
        """
        Process natural language query about players
        
        Args:
            user_question: Natural language question from user
            trace_id: Request trace ID for logging
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            logger.info(f"[{trace_id}] AI Query: {user_question}")
            
            # Step 1: Use LLM to understand intent and extract parameters
            function_call = self._extract_function_call(user_question, trace_id)
            
            if not function_call:
                return {
                    'answer': "I'm sorry, I couldn't understand your question. Please try asking about player searches, specific players, or statistics.",
                    'function_called': None,
                    'results_count': 0
                }
            
            # Step 2: Execute the function
            results = self._execute_function(function_call, trace_id)
            
            # Step 3: Use LLM to format the answer
            answer = self._format_answer(user_question, function_call, results, trace_id)
            
            return {
                'answer': answer,
                'function_called': function_call['name'],
                'parameters': function_call.get('parameters', {}),
                'results_count': len(results) if isinstance(results, list) else 1,
                'raw_results': results[:5] if isinstance(results, list) else results  # First 5 for brevity
            }
            
        except Exception as e:
            logger.error(f"[{trace_id}] AI Query error: {e}")
            return {
                'answer': f"I encountered an error processing your question: {str(e)}",
                'error': str(e)
            }
    
    def _extract_function_call(self, question: str, trace_id: str) -> Optional[Dict]:
        """
        Use LLM to extract function call from natural language
        
        This is the "intent recognition" step
        """
        try:
            # System prompt that guides the LLM
            system_prompt = f"""You are an AI assistant that helps query a baseball player database.

Available functions:
{json.dumps(self.tools, indent=2)}

User will ask questions about baseball players. Your job is to:
1. Understand their intent
2. Choose the appropriate function
3. Extract parameters from their question
4. Return ONLY a JSON object with the function call

Response format (JSON only, no explanations):
{{
    "name": "function_name",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}

Examples:
Q: "Show me players from Dominican Republic"
A: {{"name": "search_players", "parameters": {{"country": "DOM", "limit": 10}}}}

Q: "Find Babe Ruth"
A: {{"name": "get_player_by_name", "parameters": {{"first_name": "Babe", "last_name": "Ruth"}}}}

Q: "What's the average height of players?"
A: {{"name": "get_player_statistics", "parameters": {{"stat_type": "average_height"}}}}

Important:
- Heights: Convert feet/inches to cm (1 foot = 30.48cm, 1 inch = 2.54cm)
- Countries: Use standard codes (USA, DOM, VEN, MEX, etc.)
- Return ONLY JSON, no explanations
"""

            # Call LLM
            response = ollama.chat(
                model='tinyllama',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}
                ]
            )
            
            # Extract JSON from response
            content = response['message']['content']
            logger.info(f"[{trace_id}] LLM raw response: {content}")
            
            # Parse JSON (LLM might add extra text, extract JSON)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                function_call = json.loads(json_match.group())
                logger.info(f"[{trace_id}] Extracted function call: {function_call}")
                return function_call
            
            logger.warning(f"[{trace_id}] Could not extract JSON from LLM response")
            return None
            
        except Exception as e:
            logger.error(f"[{trace_id}] Error extracting function call: {e}")
            return None
    
    def _execute_function(self, function_call: Dict, trace_id: str) -> any:
        """
        Execute the function call with security validation
        
        CRITICAL: Validate all parameters to prevent injection attacks
        """
        try:
            function_name = function_call.get('name')
            parameters = function_call.get('parameters', {})
            
            logger.info(f"[{trace_id}] Executing: {function_name} with {parameters}")
            
            if function_name == 'search_players':
                # Build safe query with parameterization
                filters = []
                params = []
                
                if 'country' in parameters:
                    filters.append("birthCountry = ?")
                    params.append(parameters['country'])
                
                if 'min_height' in parameters:
                    filters.append("height >= ?")
                    params.append(parameters['min_height'])
                
                if 'max_height' in parameters:
                    filters.append("height <= ?")
                    params.append(parameters['max_height'])
                
                if 'bats' in parameters:
                    filters.append("bats = ?")
                    params.append(parameters['bats'])
                
                if 'throws' in parameters:
                    filters.append("throws = ?")
                    params.append(parameters['throws'])
                
                limit = min(parameters.get('limit', 10), 100)  # Cap at 100
                
                # Build query with filters
                query = "SELECT * FROM players"
                if filters:
                    query += " WHERE " + " AND ".join(filters)
                query += f" LIMIT ?"
                params.append(limit)
                
                # Execute safe parameterized query
                result = self.player_service.cursor.execute(query, tuple(params)).fetchall()
                players = [self.player_service.convert_row_to_dict(row) for row in result]
                
                logger.info(f"[{trace_id}] Found {len(players)} players")
                return players
                
            elif function_name == 'get_player_by_name':
                first_name = parameters.get('first_name', '')
                last_name = parameters.get('last_name', '')
                
                query = "SELECT * FROM players WHERE "
                params = []
                
                if first_name and last_name:
                    query += "nameFirst = ? AND nameLast = ?"
                    params = [first_name, last_name]
                elif last_name:
                    query += "nameLast = ?"
                    params = [last_name]
                else:
                    return []
                
                query += " LIMIT 10"
                result = self.player_service.cursor.execute(query, tuple(params)).fetchall()
                players = [self.player_service.convert_row_to_dict(row) for row in result]
                
                return players
                
            elif function_name == 'get_player_statistics':
                stat_type = parameters.get('stat_type')
                country = parameters.get('country')
                
                if stat_type == 'average_height':
                    query = "SELECT AVG(height) as avg_height, COUNT(*) as count FROM players"
                    params = []
                    if country:
                        query += " WHERE birthCountry = ?"
                        params.append(country)
                    
                    result = self.player_service.cursor.execute(query, tuple(params)).fetchone()
                    return {
                        'average_height_cm': round(result[0], 2) if result[0] else 0,
                        'count': result[1]
                    }
                
                elif stat_type == 'average_weight':
                    query = "SELECT AVG(weight) as avg_weight, COUNT(*) as count FROM players"
                    params = []
                    if country:
                        query += " WHERE birthCountry = ?"
                        params.append(country)
                    
                    result = self.player_service.cursor.execute(query, tuple(params)).fetchone()
                    return {
                        'average_weight_kg': round(result[0], 2) if result[0] else 0,
                        'count': result[1]
                    }
                
                elif stat_type == 'count_by_country':
                    query = """
                        SELECT birthCountry, COUNT(*) as count 
                        FROM players 
                        GROUP BY birthCountry 
                        ORDER BY count DESC 
                        LIMIT 10
                    """
                    result = self.player_service.cursor.execute(query).fetchall()
                    return [{'country': row[0], 'count': row[1]} for row in result]
            
            return []
            
        except Exception as e:
            logger.error(f"[{trace_id}] Error executing function: {e}")
            raise
    
    def _format_answer(self, question: str, function_call: Dict, results: any, trace_id: str) -> str:
        """
        Use LLM to format results into natural language answer
        """
        try:
            # Create context for LLM
            context = f"""User asked: "{question}"

We called function: {function_call['name']}
With parameters: {json.dumps(function_call.get('parameters', {}), indent=2)}

Results:
{json.dumps(results, indent=2) if not isinstance(results, str) else results}

Please provide a natural, helpful answer to the user's question based on these results.
Keep it concise and friendly. If there are many results, summarize and mention the total count."""

            response = ollama.chat(
                model='tinyllama',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant that explains baseball player data in a friendly, concise way.'
                    },
                    {
                        'role': 'user',
                        'content': context
                    }
                ]
            )
            
            answer = response['message']['content']
            logger.info(f"[{trace_id}] Formatted answer: {answer[:100]}...")
            
            return answer
            
        except Exception as e:
            logger.error(f"[{trace_id}] Error formatting answer: {e}")
            # Fallback to simple answer
            if isinstance(results, list):
                return f"I found {len(results)} players matching your criteria."
            else:
                return f"Here's what I found: {json.dumps(results)}"
```

### Add Endpoint to app.py:

```python
# app.py - Add AI query endpoint

from ai_query_service import AIQueryService

@app.route('/v1/ai/query', methods=['POST'])
@require_auth()
def ai_query():
    """
    Natural language query endpoint using AI
    
    Request body:
    {
        "question": "Show me all players from USA taller than 6 feet"
    }
    
    Response:
    {
        "answer": "I found 45 players from USA...",
        "function_called": "search_players",
        "parameters": {...},
        "results_count": 45,
        "raw_results": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'error': {
                    'code': 'INVALID_INPUT',
                    'message': 'Missing required field: question',
                    'trace_id': g.trace_id
                }
            }), 400
        
        question = data['question']
        
        # Rate limit AI queries (more expensive)
        # In production: check rate limit in Redis
        
        ai_service = AIQueryService()
        result = ai_service.query(question, trace_id=g.trace_id)
        
        logger.info(
            f"[{g.trace_id}] User {g.current_user.get('email')} "
            f"AI query: {question[:50]}... → {result.get('results_count', 0)} results"
        )
        
        return jsonify({
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"[{g.trace_id}] Error in AI query: {e}")
        return jsonify({
            'error': {
                'code': 'AI_QUERY_ERROR',
                'message': 'Failed to process AI query',
                'trace_id': g.trace_id
            }
        }), 500

# Add examples endpoint for documentation
@app.route('/v1/ai/examples', methods=['GET'])
def ai_query_examples():
    """Get example queries for AI endpoint"""
    examples = [
        {
            "question": "Show me all players from Dominican Republic",
            "description": "Search players by country"
        },
        {
            "question": "Find players taller than 6 feet who bat left",
            "description": "Search with multiple filters"
        },
        {
            "question": "Who is Babe Ruth?",
            "description": "Get specific player by name"
        },
        {
            "question": "What's the average height of players?",
            "description": "Get statistics"
        },
        {
            "question": "How many players are from each country?",
            "description": "Get aggregated statistics"
        }
    ]
    
    return jsonify({
        'data': {
            'examples': examples,
            'usage': {
                'endpoint': '/v1/ai/query',
                'method': 'POST',
                'body': {
                    'question': 'Your natural language question here'
                },
                'authentication': 'Required (Bearer token)'
            }
        }
    }), 200
```

---

## 🎤 Interview Talking Points for AI Feature

### **When Implementing:**

> "I'm implementing an AI-powered natural language query interface. This demonstrates several senior-level AI integration patterns:
>
> **1. LLM Tool/Function Calling**
> Instead of having the LLM generate SQL directly (dangerous!), I define a set of safe functions it can call. The LLM acts as an intent recognition layer, translating natural language to function calls with parameters.
>
> **2. Security-First Approach**
> Even though an LLM is involved, all database queries use parameterized statements. The LLM never generates raw SQL - it only populates parameters that we validate. This prevents SQL injection even if the LLM is compromised or malicious input is provided.
>
> **3. Prompt Engineering**
> The system prompt carefully guides the LLM to return structured JSON. I provide examples (few-shot learning) and specify output format strictly. In production, we'd use a more powerful model like GPT-4 with better instruction following.
>
> **4. Error Handling & Fallbacks**
> LLMs are unreliable - they might return malformed JSON or misunderstand queries. I have parsing fallbacks, regex extraction for JSON, and graceful degradation if the LLM fails. We log everything for monitoring.
>
> **5. RAG Pattern (Retrieval-Augmented Generation)**
> This is a basic RAG implementation: User question → Retrieve data from database → Augment LLM prompt with data → Generate natural language response. In production, we'd add vector embeddings for semantic search.
>
> **6. Cost & Performance Considerations**
> LLM calls are expensive (time and money). I'd add:
> - Caching for common queries
> - Rate limiting (stricter for AI endpoints)
> - Async processing for slow queries
> - Circuit breaker if LLM service is down
>
> **7. Observability**
> I log the LLM's raw response, the extracted function call, and the final answer. This lets us monitor:
> - Accuracy: Is the LLM extracting intent correctly?
> - Performance: How long do LLM calls take?
> - Cost: How many tokens are we using?
>
> **In Production at Intuit:**
> For customer-facing AI features, I'd add:
> - Content filtering (prevent toxic responses)
> - PII detection (don't expose sensitive data)
> - Audit logging (all AI interactions)
> - Human-in-the-loop for sensitive operations
> - A/B testing different prompts
> - Model versioning and rollback capability"

### **Example Usage:**

```bash
# Natural language query
curl -X POST http://localhost:8000/v1/ai/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me all players from USA who are taller than 6 feet"
  }'

# Response
{
  "data": {
    "answer": "I found 45 players from the USA who are taller than 6 feet (183 cm). Here are some notable ones: Babe Ruth, Lou Gehrig, and Mickey Mantle were all over 6 feet tall and became baseball legends.",
    "function_called": "search_players",
    "parameters": {
      "country": "USA",
      "min_height": 183,
      "limit": 10
    },
    "results_count": 45,
    "raw_results": [...]
  }
}
```

---

## 🎯 Recommendation for Your 75-Minute Demo

### **Option A: Security + Auth + Pagination (Safe)**
- ✅ Time: Fits well in 75 minutes
- ✅ Complexity: Appropriate for senior
- ✅ Demonstrates: Security, architecture, performance
- ❌ AI integration: Limited

### **Option B: Security + Auth + AI Query (Impressive!)** ⭐ RECOMMENDED
- ✅ Time: Tight but doable (need to practice)
- ✅ Complexity: Senior+ level
- ✅ Demonstrates: Security, AI integration, modern patterns
- ✅ Directly addresses AI assessment round
- ✅ Very impressive and current (LLM tool calling is cutting-edge)

### **Option C: All Three (Ambitious)**
- ⚠️ Time: Might run over 75 minutes
- ✅ Complexity: Definitely senior level
- ✅ Very impressive BUT risky if you run out of time
- ❌ Recommendation: Only if you're VERY comfortable with the code

---

## 📅 Modified Timeline (With AI Feature)

### **Option B Timeline:**

| Time | Task | What to Say |
|------|------|-------------|
| 0-5 min | Introduction | Standard opening + mention AI feature |
| 5-15 min | Fix SQL injection | "Critical security issue..." |
| 15-35 min | JWT Auth | "Implementing stateless authentication..." |
| 35-60 min | AI Query Feature | "Now for AI integration using LLM tool calling..." |
| 60-75 min | Demo & Discussion | Show examples, discuss production considerations |

---

## 💡 My Recommendation

**Go with Option B** (Security + Auth + AI Query):

**Why:**
1. **Directly addresses AI assessment** - You'll impress in both technical AND AI rounds
2. **Modern & Relevant** - LLM tool calling is cutting-edge (2024/2025 tech)
3. **Shows depth** - Not just CRUD, but AI integration with proper security
4. **Differentiation** - Most candidates won't have this
5. **Conversation starter** - Interviewers will ask about your AI approach

**Skip or minimize:**
- Caching (less impressive than AI)
- Advanced pagination (nice-to-have, not critical)

**Time management:**
- Practice the AI implementation 2-3 times
- Have the code ready to paste (less typing during demo)
- If running short on time, skip the "format answer" part and just return raw results

---

Would you like me to:
1. Create the complete AI implementation files ready to paste?
2. Modify the DEMO_IMPLEMENTATION.md to include the AI feature as primary?
3. Create test cases specifically for the AI feature?
4. Add the AI feature to the Postman collection?

Let me know and I'll update everything! 🚀

