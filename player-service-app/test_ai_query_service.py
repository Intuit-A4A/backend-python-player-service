"""
Unit tests for AI Query Service
Demonstrates testing practices for AI/LLM integration
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from ai_query_service import AIQueryService


class TestAIQueryService:
    """
    Unit tests for AI Query Service
    
    Testing AI systems requires special considerations:
    - Mock external LLM calls (expensive, slow, unreliable)
    - Test both happy path and error cases
    - Test security validations
    - Test fallback mechanisms
    """
    
    @pytest.fixture
    def mock_player_service(self):
        """Mock PlayerService to avoid database dependency"""
        mock_service = Mock()
        mock_service.cursor = Mock()
        mock_service.convert_row_to_dict = Mock(
            return_value={
                'playerId': 'test123',
                'nameFirst': 'Test',
                'nameLast': 'Player',
                'birthCountry': 'USA',
                'height': 185,
                'weight': 85
            }
        )
        mock_service.close = Mock()
        return mock_service
    
    @pytest.fixture
    def ai_service(self, mock_player_service):
        """Create AIQueryService with mocked dependencies"""
        with patch('ai_query_service.PlayerService', return_value=mock_player_service):
            service = AIQueryService()
            service.player_service = mock_player_service
            return service
    
    # ========================================
    # Test 1: Successful Query Processing
    # ========================================
    
    @patch('ai_query_service.ollama')
    def test_query_success_search_players(self, mock_ollama, ai_service):
        """
        Test successful natural language query that searches players
        
        This tests the complete flow:
        1. User asks natural language question
        2. LLM extracts function call
        3. Function executes with parameterized query
        4. LLM formats response
        """
        # Arrange: Mock LLM responses
        mock_ollama.chat.side_effect = [
            # First call: Extract function call
            {
                'message': {
                    'content': '{"name": "search_players", "parameters": {"country": "USA", "limit": 10}}'
                }
            },
            # Second call: Format answer
            {
                'message': {
                    'content': 'I found 1 player from the USA in our database.'
                }
            }
        ]
        
        # Mock database response
        ai_service.player_service.cursor.execute.return_value.fetchall.return_value = [
            ('test123', 'Test', 'Player', 1990, 1, 1, 'USA', 'CA', 'LA', 185, 85, 'R', 'R', '2010-01-01', '2020-01-01')
        ]
        
        # Act: Execute query
        result = ai_service.query(
            "Show me players from USA",
            trace_id="test-trace-123"
        )
        
        # Assert: Verify response
        assert result['function_called'] == 'search_players'
        assert result['parameters']['country'] == 'USA'
        assert result['results_count'] == 1
        assert 'answer' in result
        assert 'I found' in result['answer']
        
        # Verify LLM was called twice (extract + format)
        assert mock_ollama.chat.call_count == 2
        
        # Verify database query was called with parameterized query
        ai_service.player_service.cursor.execute.assert_called_once()
        call_args = ai_service.player_service.cursor.execute.call_args
        assert '?' in call_args[0][0]  # Query has placeholder
        assert isinstance(call_args[0][1], tuple)  # Parameters as tuple
    
    # ========================================
    # Test 2: SQL Injection Prevention
    # ========================================
    
    @patch('ai_query_service.ollama')
    def test_sql_injection_prevention(self, mock_ollama, ai_service):
        """
        Test that SQL injection attempts are prevented
        
        CRITICAL: Even if LLM returns malicious input,
        parameterized queries prevent SQL injection
        """
        # Arrange: LLM tries to inject SQL (malicious or compromised)
        mock_ollama.chat.return_value = {
            'message': {
                'content': '{"name": "search_players", "parameters": {"country": "USA\'; DROP TABLE players; --", "limit": 10}}'
            }
        }
        
        ai_service.player_service.cursor.execute.return_value.fetchall.return_value = []
        
        # Act: Execute query
        result = ai_service._extract_function_call(
            "malicious query",
            trace_id="test-injection"
        )
        
        # Assert: Function call extracted (LLM might be compromised)
        assert result is not None
        assert result['parameters']['country'] == "USA'; DROP TABLE players; --"
        
        # Now execute - should use parameterized query
        ai_service._execute_function(result, "test-injection")
        
        # Verify: Parameterized query used (safe!)
        call_args = ai_service.player_service.cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        # Query has placeholders, not direct injection
        assert '?' in query
        assert 'DROP TABLE' not in query  # Injection not in query
        assert "USA'; DROP TABLE players; --" in params  # Safely parameterized
    
    # ========================================
    # Test 3: LLM Failure Handling
    # ========================================
    
    @patch('ai_query_service.ollama')
    def test_llm_failure_graceful_degradation(self, mock_ollama, ai_service):
        """
        Test graceful handling when LLM fails or returns invalid JSON
        
        LLMs are unreliable - we need fallback mechanisms
        """
        # Arrange: LLM returns invalid JSON
        mock_ollama.chat.return_value = {
            'message': {
                'content': 'I cannot understand this query, sorry!'  # No JSON
            }
        }
        
        # Act: Execute query
        result = ai_service.query(
            "some random text",
            trace_id="test-failure"
        )
        
        # Assert: Graceful failure with helpful message
        assert result['function_called'] is None
        assert 'sorry' in result['answer'].lower() or 'couldn\'t understand' in result['answer'].lower()
        assert 'examples' in result  # Provide examples to help user
    
    # ========================================
    # Test 4: Parameter Validation
    # ========================================
    
    def test_search_players_parameter_validation(self, ai_service):
        """
        Test that function parameters are validated before execution
        
        Defense in depth: Validate even if LLM provided the parameters
        """
        # Arrange: Mock database
        ai_service.player_service.cursor.execute.return_value.fetchall.return_value = []
        
        # Act: Try with excessive limit (should be capped)
        function_call = {
            'name': 'search_players',
            'parameters': {
                'country': 'USA',
                'limit': 99999  # Excessive
            }
        }
        
        ai_service._execute_function(function_call, "test-validation")
        
        # Assert: Limit was capped at 100
        call_args = ai_service.player_service.cursor.execute.call_args
        params = call_args[0][1]
        # Last parameter is limit
        assert params[-1] == 100  # Capped at max
    
    # ========================================
    # Test 5: Get Player by Name
    # ========================================
    
    @patch('ai_query_service.ollama')
    def test_get_player_by_name(self, mock_ollama, ai_service):
        """Test searching for specific player by name"""
        # Arrange
        mock_ollama.chat.side_effect = [
            {
                'message': {
                    'content': '{"name": "get_player_by_name", "parameters": {"first_name": "Babe", "last_name": "Ruth"}}'
                }
            },
            {
                'message': {
                    'content': 'Babe Ruth was a legendary baseball player.'
                }
            }
        ]
        
        ai_service.player_service.cursor.execute.return_value.fetchall.return_value = [
            ('ruthba01', 'Babe', 'Ruth', 1895, 2, 6, 'USA', 'MD', 'Baltimore', 188, 98, 'L', 'L', '1914-07-11', '1935-05-30')
        ]
        
        # Act
        result = ai_service.query("Who is Babe Ruth?", trace_id="test-babe-ruth")
        
        # Assert
        assert result['function_called'] == 'get_player_by_name'
        assert result['parameters']['first_name'] == 'Babe'
        assert result['parameters']['last_name'] == 'Ruth'
        assert result['results_count'] == 1
        assert 'Babe Ruth' in result['answer']
    
    # ========================================
    # Test 6: Statistics Query
    # ========================================
    
    @patch('ai_query_service.ollama')
    def test_get_statistics(self, mock_ollama, ai_service):
        """Test statistical aggregation queries"""
        # Arrange
        mock_ollama.chat.side_effect = [
            {
                'message': {
                    'content': '{"name": "get_player_statistics", "parameters": {"stat_type": "average_height"}}'
                }
            },
            {
                'message': {
                    'content': 'The average height of players is 182.5 cm or about 6 feet.'
                }
            }
        ]
        
        # Mock database returning average
        ai_service.player_service.cursor.execute.return_value.fetchone.return_value = (182.5, 1000)
        
        # Act
        result = ai_service.query(
            "What's the average height of players?",
            trace_id="test-stats"
        )
        
        # Assert
        assert result['function_called'] == 'get_player_statistics'
        assert result['parameters']['stat_type'] == 'average_height'
        assert 'average_height_cm' in result['raw_results']
        assert result['raw_results']['average_height_cm'] == 182.5
    
    # ========================================
    # Test 7: Complex Query with Multiple Filters
    # ========================================
    
    def test_search_with_multiple_filters(self, ai_service):
        """Test search with multiple filter parameters"""
        # Arrange
        ai_service.player_service.cursor.execute.return_value.fetchall.return_value = []
        
        # Act
        function_call = {
            'name': 'search_players',
            'parameters': {
                'country': 'USA',
                'min_height': 183,
                'bats': 'L',
                'throws': 'R',
                'limit': 20
            }
        }
        
        ai_service._execute_function(function_call, "test-multi-filter")
        
        # Assert: All filters applied
        call_args = ai_service.player_service.cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        # Query should have all WHERE clauses
        assert 'birthCountry = ?' in query
        assert 'height >= ?' in query
        assert 'bats = ?' in query
        assert 'throws = ?' in query
        
        # Parameters should match
        assert 'USA' in params
        assert 183 in params
        assert 'L' in params
        assert 'R' in params
    
    # ========================================
    # Test 8: Error Handling
    # ========================================
    
    @patch('ai_query_service.ollama')
    def test_database_error_handling(self, mock_ollama, ai_service):
        """Test handling of database errors during query execution"""
        # Arrange: LLM succeeds but database fails
        mock_ollama.chat.return_value = {
            'message': {
                'content': '{"name": "search_players", "parameters": {"country": "USA"}}'
            }
        }
        
        # Simulate database error
        ai_service.player_service.cursor.execute.side_effect = Exception("Database connection lost")
        
        # Act
        result = ai_service.query("Show me players", trace_id="test-db-error")
        
        # Assert: Error handled gracefully
        assert 'error' in result
        assert 'trace_id' in result
    
    # ========================================
    # Test 9: Empty Results Handling
    # ========================================
    
    @patch('ai_query_service.ollama')
    def test_empty_results(self, mock_ollama, ai_service):
        """Test handling when query returns no results"""
        # Arrange
        mock_ollama.chat.side_effect = [
            {
                'message': {
                    'content': '{"name": "search_players", "parameters": {"country": "INVALID"}}'
                }
            },
            {
                'message': {
                    'content': 'I did not find any players matching your criteria.'
                }
            }
        ]
        
        ai_service.player_service.cursor.execute.return_value.fetchall.return_value = []
        
        # Act
        result = ai_service.query(
            "Show me players from INVALID country",
            trace_id="test-empty"
        )
        
        # Assert
        assert result['results_count'] == 0
        assert 'not find' in result['answer'].lower() or 'no' in result['answer'].lower()


# ========================================
# Integration Test (Optional)
# ========================================

class TestAIQueryServiceIntegration:
    """
    Integration tests with actual Ollama (optional)
    Only run if Ollama is available
    """
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration", default=False),
        reason="Integration tests require --run-integration flag"
    )
    def test_real_ollama_integration(self):
        """
        Test with real Ollama instance
        
        Run with: pytest test_ai_query_service.py --run-integration
        """
        try:
            import ollama
            ollama.chat(model='tinyllama', messages=[{'role': 'user', 'content': 'test'}])
            
            # If Ollama is available, test real query
            service = AIQueryService()
            result = service.query("Show me players from USA", trace_id="integration-test")
            
            assert 'answer' in result
            assert 'function_called' in result
            
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")


# ========================================
# Performance Test
# ========================================

class TestAIQueryServicePerformance:
    """
    Performance tests to ensure AI queries don't timeout
    """
    
    @patch('ai_query_service.ollama')
    def test_query_performance(self, mock_ollama, ai_service):
        """Test that query completes within reasonable time"""
        import time
        
        # Arrange: Fast mocked responses
        mock_ollama.chat.side_effect = [
            {
                'message': {
                    'content': '{"name": "search_players", "parameters": {"country": "USA"}}'
                }
            },
            {
                'message': {
                    'content': 'I found players from USA.'
                }
            }
        ]
        
        ai_service.player_service.cursor.execute.return_value.fetchall.return_value = []
        
        # Act: Measure time
        start = time.time()
        result = ai_service.query("Show me players", trace_id="perf-test")
        elapsed = time.time() - start
        
        # Assert: Completes quickly (mocked should be < 1 second)
        assert elapsed < 1.0
        assert 'answer' in result


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])

