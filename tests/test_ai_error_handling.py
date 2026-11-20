"""Tests for AI API error handling."""

import os
import logging
import pytest
from unittest.mock import Mock, patch
from users.questions.prompting import get_response_from_prompt


def test_hf_token_required():
    """HF_TOKEN environment variable should be validated."""
    if 'HF_TOKEN' in os.environ:
        del os.environ['HF_TOKEN']
    
    with pytest.raises(KeyError):
        get_response_from_prompt('test_unit', 1, 'test prompt')


def test_error_logging_no_credentials_exposed(caplog):
    """Error logging should not expose sensitive credentials."""
    os.environ['HF_TOKEN'] = 'test-token-12345'
    
    with patch('users.questions.prompting.InferenceClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.chat.completions.create.side_effect = Exception("API Error")
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(Exception):
                get_response_from_prompt('unit1', 1, 'prompt')
        
        # Verify token is not in logs
        assert 'test-token-12345' not in caplog.text
        assert 'HF_TOKEN' not in caplog.text
        
        # Verify error is logged but without full traceback
        assert 'API error' in caplog.text or 'Exception' in caplog.text


def test_error_handling_preserves_exception_type():
    """Should re-raise the original exception type."""
    os.environ['HF_TOKEN'] = 'test-token'
    
    with patch('users.questions.prompting.InferenceClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # Test with specific exception
        from huggingface_hub.errors import BadRequestError
        mock_instance.chat.completions.create.side_effect = BadRequestError("Invalid request")
        
        with pytest.raises(BadRequestError):
            get_response_from_prompt('unit1', 1, 'prompt')
