"""
AI-Powered Natural Language Query Service
Demonstrates LLM tool/function calling pattern for senior-level AI integration
"""

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
    - LLM tool/function calling (ChatGPT plugins pattern)
    - Prompt engineering with few-shot learning
    - Security-first AI (no raw SQL generation)
    - Error handling for unreliable LLMs
    - Structured output parsing
    - RAG pattern implementation
    """
    
    def __init__(self):
        self.player_service = PlayerService()
        
        # Define available tools/functions the LLM can call
        # This is the "function calling" or "tool use" pattern
        self.tools = [
            {
                "name": "search_players",
                "description": "Search for baseball players with various filters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "Filter by birth country (e.g., 'USA', 'DOM', 'VEN')"
                        },
                        "min_height": {
                            "type": "integer",
                            "description": "Minimum height in centimeters (6 feet = 183cm)"
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
                "description": "Get specific player(s) by name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "Player's first name"
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Player's last name (required)"
                        }
                    },
                    "required": ["last_name"]
                }
            },
            {
                "name": "get_player_statistics",
                "description": "Get statistical aggregations about players",
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
                            "description": "Optional: filter statistics by country"
                        }
                    },
                    "required": ["stat_type"]
                }
            }
        ]
    
    def query(self, user_question: str, trace_id: str = "unknown") -> Dict:
        """
        Process natural language query about players using LLM
        
        This implements a simple RAG (Retrieval-Augmented Generation) pattern:
        1. User asks question
        2. LLM extracts intent and parameters (retrieval planning)
        3. Execute function to retrieve data
        4. LLM formats answer with retrieved data (generation)
        
        Args:
            user_question: Natural language question from user
            trace_id: Request trace ID for logging
            
        Returns:
            Dictionary with answer, metadata, and raw results
        """
        try:
            logger.info(f"[{trace_id}] AI Query received: {user_question}")
            
            # Step 1: Use LLM to understand intent and extract parameters
            # This is the "intent recognition" or "function calling" step
            function_call = self._extract_function_call(user_question, trace_id)
            
            if not function_call:
                return {
                    'answer': "I'm sorry, I couldn't understand your question. Please try asking about player searches, specific players, or statistics.",
                    'function_called': None,
                    'results_count': 0,
                    'examples': [
                        "Show me players from USA taller than 6 feet",
                        "Find Babe Ruth",
                        "What's the average height of players?"
                    ]
                }
            
            # Step 2: Execute the function with security validation
            results = self._execute_function(function_call, trace_id)
            
            # Step 3: Use LLM to format the answer naturally
            answer = self._format_answer(user_question, function_call, results, trace_id)
            
            return {
                'answer': answer,
                'function_called': function_call['name'],
                'parameters': function_call.get('parameters', {}),
                'results_count': len(results) if isinstance(results, list) else 1,
                'raw_results': results[:5] if isinstance(results, list) else results,  # First 5 only
                'trace_id': trace_id
            }
            
        except Exception as e:
            logger.error(f"[{trace_id}] AI Query error: {e}", exc_info=True)
            return {
                'answer': f"I encountered an error processing your question. Please try rephrasing or contact support.",
                'error': str(e),
                'trace_id': trace_id
            }
    
    def _extract_function_call(self, question: str, trace_id: str) -> Optional[Dict]:
        """
        Use LLM to extract function call from natural language
        
        This demonstrates:
        - Prompt engineering (system prompt + few-shot examples)
        - Structured output from LLM (JSON extraction)
        - Error handling for unreliable LLM outputs
        
        Production improvements:
        - Use GPT-4 instead of tinyllama (better instruction following)
        - Add retry logic with exponential backoff
        - Cache common queries
        - Add function calling via OpenAI's native API
        """
        try:
            # System prompt guides the LLM's behavior
            # This is critical for getting reliable structured output
            system_prompt = f"""You are an AI assistant that converts natural language questions into function calls for a baseball player database.

Available functions:
{json.dumps(self.tools, indent=2)}

Your job:
1. Understand the user's intent
2. Choose the appropriate function
3. Extract parameters from their question
4. Return ONLY a valid JSON object

Response format (JSON only, no markdown, no explanations):
{{
    "name": "function_name",
    "parameters": {{
        "param1": "value1"
    }}
}}

Examples (few-shot learning):
Q: "Show me players from Dominican Republic"
A: {{"name": "search_players", "parameters": {{"country": "DOM", "limit": 10}}}}

Q: "Find players taller than 6 feet who bat left"
A: {{"name": "search_players", "parameters": {{"min_height": 183, "bats": "L", "limit": 10}}}}

Q: "Who is Babe Ruth?"
A: {{"name": "get_player_by_name", "parameters": {{"first_name": "Babe", "last_name": "Ruth"}}}}

Q: "What's the average height?"
A: {{"name": "get_player_statistics", "parameters": {{"stat_type": "average_height"}}}}

Important conversion rules:
- Heights: 6 feet = 183cm, 1 foot = 30.48cm, 1 inch = 2.54cm
- Countries: Use codes (USA, DOM, VEN, MEX, CAN, etc.)
- Return ONLY JSON, no explanations or markdown
"""

            # Call Ollama LLM
            # In production, use OpenAI GPT-4 for better reliability
            response = ollama.chat(
                model='tinyllama',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}
                ]
            )
            
            content = response['message']['content']
            logger.info(f"[{trace_id}] LLM raw response: {content}")
            
            # Extract JSON from response
            # LLM might add extra text, so we extract JSON with regex
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                function_call = json.loads(json_match.group())
                logger.info(f"[{trace_id}] Extracted function call: {function_call}")
                
                # Validate function exists
                valid_functions = [tool['name'] for tool in self.tools]
                if function_call.get('name') not in valid_functions:
                    logger.warning(f"[{trace_id}] Invalid function: {function_call.get('name')}")
                    return None
                
                return function_call
            
            logger.warning(f"[{trace_id}] Could not extract JSON from LLM response")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"[{trace_id}] JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"[{trace_id}] Error extracting function call: {e}", exc_info=True)
            return None
    
    def _execute_function(self, function_call: Dict, trace_id: str) -> any:
        """
        Execute the function call with security validation
        
        CRITICAL SECURITY:
        - NEVER pass user input directly to SQL
        - Always use parameterized queries
        - Validate all parameters before use
        - Log all executions for audit
        
        This prevents SQL injection even if LLM is compromised or
        malicious input is provided.
        """
        try:
            function_name = function_call.get('name')
            parameters = function_call.get('parameters', {})
            
            logger.info(f"[{trace_id}] Executing: {function_name} with params: {parameters}")
            
            if function_name == 'search_players':
                return self._search_players(parameters, trace_id)
                
            elif function_name == 'get_player_by_name':
                return self._get_player_by_name(parameters, trace_id)
                
            elif function_name == 'get_player_statistics':
                return self._get_player_statistics(parameters, trace_id)
            
            else:
                logger.error(f"[{trace_id}] Unknown function: {function_name}")
                return []
            
        except Exception as e:
            logger.error(f"[{trace_id}] Error executing function: {e}", exc_info=True)
            raise
    
    def _search_players(self, parameters: Dict, trace_id: str) -> List[Dict]:
        """Search players with filters - uses parameterized queries"""
        filters = []
        params = []
        
        # Build WHERE clauses with parameterization (SQL injection safe)
        if 'country' in parameters:
            filters.append("birthCountry = ?")
            params.append(parameters['country'])
        
        if 'min_height' in parameters:
            filters.append("height >= ?")
            params.append(int(parameters['min_height']))
        
        if 'max_height' in parameters:
            filters.append("height <= ?")
            params.append(int(parameters['max_height']))
        
        if 'bats' in parameters and parameters['bats'] in ['L', 'R', 'B']:
            filters.append("bats = ?")
            params.append(parameters['bats'])
        
        if 'throws' in parameters and parameters['throws'] in ['L', 'R']:
            filters.append("throws = ?")
            params.append(parameters['throws'])
        
        # Cap limit to prevent excessive queries
        limit = min(int(parameters.get('limit', 10)), 100)
        
        # Build safe parameterized query
        query = "SELECT * FROM players"
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " LIMIT ?"
        params.append(limit)
        
        # Execute with parameterization - SQL injection safe!
        result = self.player_service.cursor.execute(query, tuple(params)).fetchall()
        players = [self.player_service.convert_row_to_dict(row) for row in result]
        
        logger.info(f"[{trace_id}] Found {len(players)} players")
        return players
    
    def _get_player_by_name(self, parameters: Dict, trace_id: str) -> List[Dict]:
        """Get player by name - parameterized queries"""
        first_name = parameters.get('first_name', '')
        last_name = parameters.get('last_name', '')
        
        if not last_name:
            return []
        
        query = "SELECT * FROM players WHERE "
        params = []
        
        if first_name and last_name:
            query += "nameFirst = ? AND nameLast = ?"
            params = [first_name, last_name]
        else:
            query += "nameLast = ?"
            params = [last_name]
        
        query += " LIMIT 10"
        
        result = self.player_service.cursor.execute(query, tuple(params)).fetchall()
        players = [self.player_service.convert_row_to_dict(row) for row in result]
        
        logger.info(f"[{trace_id}] Found {len(players)} players named {last_name}")
        return players
    
    def _get_player_statistics(self, parameters: Dict, trace_id: str) -> Dict:
        """Get aggregated statistics"""
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
                'average_height_feet': round(result[0] / 30.48, 2) if result[0] else 0,
                'count': result[1],
                'country': country or 'all'
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
                'average_weight_lbs': round(result[0] * 2.205, 2) if result[0] else 0,
                'count': result[1],
                'country': country or 'all'
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
            return {
                'countries': [{'country': row[0], 'count': row[1]} for row in result],
                'total_countries': len(result)
            }
        
        return {}
    
    def _format_answer(self, question: str, function_call: Dict, results: any, trace_id: str) -> str:
        """
        Use LLM to format results into natural language answer
        
        This is the "generation" part of RAG (Retrieval-Augmented Generation)
        We augment the LLM's context with retrieved data
        """
        try:
            # Create context for LLM with retrieved data
            context = f"""User asked: "{question}"

We executed: {function_call['name']}
With parameters: {json.dumps(function_call.get('parameters', {}), indent=2)}

Retrieved data:
{json.dumps(results, indent=2) if not isinstance(results, str) else results}

Please provide a natural, helpful, and concise answer to the user's question based on these results.
If there are many results, summarize key points and mention the total count."""

            response = ollama.chat(
                model='tinyllama',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant that explains baseball player data in a friendly, concise way. Keep responses under 3 sentences.'
                    },
                    {
                        'role': 'user',
                        'content': context
                    }
                ]
            )
            
            answer = response['message']['content'].strip()
            logger.info(f"[{trace_id}] Formatted answer: {answer[:100]}...")
            
            return answer
            
        except Exception as e:
            logger.error(f"[{trace_id}] Error formatting answer: {e}")
            # Fallback to simple answer without LLM
            if isinstance(results, list):
                return f"I found {len(results)} players matching your criteria."
            elif isinstance(results, dict) and 'count' in results:
                return f"Statistics: {json.dumps(results)}"
            else:
                return f"Here's what I found: {json.dumps(results)}"
    
    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'player_service'):
            self.player_service.close()

