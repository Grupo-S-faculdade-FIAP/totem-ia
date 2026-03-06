"""
Tests for the prompts/ module.

Covers:
    prompts/__init__.py
    prompts/agents_config.py
    prompts/sustainability_agent.py
    prompts/sustainability_config.py
    prompts/sustainability_prompts.py
"""
import pytest


# =============================================================================
# prompts/__init__.py
# =============================================================================

class TestPromptsPackageInit:
    """Covers prompts/__init__.py lines 11-15."""

    def test_import_prompts_package_exports(self):
        """Package exports get_agent, list_agents, AGENTS, DEFAULT_CONFIG."""
        import prompts
        assert hasattr(prompts, "get_agent")
        assert hasattr(prompts, "list_agents")
        assert hasattr(prompts, "AGENTS")
        assert hasattr(prompts, "DEFAULT_CONFIG")

    def test_prompts_version(self):
        import prompts
        assert prompts.__version__ == "1.0.0"

    def test_prompts_all_list(self):
        import prompts
        assert "get_agent" in prompts.__all__
        assert "list_agents" in prompts.__all__
        assert "AGENTS" in prompts.__all__
        assert "DEFAULT_CONFIG" in prompts.__all__

    def test_package_get_agent(self):
        from prompts import get_agent
        agent = get_agent("sustainability")
        assert isinstance(agent, dict)

    def test_package_list_agents(self):
        from prompts import list_agents
        agents = list_agents()
        assert isinstance(agents, dict)
        assert "sustainability" in agents


# =============================================================================
# prompts/agents_config.py
# =============================================================================

class TestAgentsConfig:
    """Covers prompts/agents_config.py lines 14-64."""

    def test_agents_dict_structure(self):
        from prompts.agents_config import AGENTS
        assert "sustainability" in AGENTS
        agent = AGENTS["sustainability"]
        assert "system_prompt" in agent
        assert "user_prompt" in agent
        assert "config" in agent
        assert "metadata" in agent
        assert "description" in agent

    def test_default_config_keys(self):
        from prompts.agents_config import DEFAULT_CONFIG
        assert DEFAULT_CONFIG["timeout"] == 30
        assert DEFAULT_CONFIG["retry_attempts"] == 3
        assert DEFAULT_CONFIG["cache_enabled"] is True
        assert DEFAULT_CONFIG["cache_duration"] == 86400

    def test_sustainability_config_values(self):
        from prompts.agents_config import SUSTAINABILITY_CONFIG
        assert SUSTAINABILITY_CONFIG["model"] == "gpt-3.5-turbo"
        assert SUSTAINABILITY_CONFIG["temperature"] == 0.7
        assert SUSTAINABILITY_CONFIG["max_tokens"] == 500

    def test_sustainability_metadata(self):
        from prompts.agents_config import SUSTAINABILITY_METADATA
        assert SUSTAINABILITY_METADATA["version"] == "1.0"
        assert "name" in SUSTAINABILITY_METADATA
        assert "description" in SUSTAINABILITY_METADATA

    def test_get_agent_sustainability(self):
        from prompts.agents_config import get_agent
        agent = get_agent("sustainability")
        assert isinstance(agent, dict)
        assert agent["config"]["model"] == "gpt-3.5-turbo"

    def test_get_agent_raises_for_unknown(self):
        from prompts.agents_config import get_agent
        with pytest.raises(ValueError, match="não encontrado"):
            get_agent("nonexistent_agent_xyz")

    def test_get_agent_error_message_lists_available(self):
        from prompts.agents_config import get_agent
        with pytest.raises(ValueError) as exc_info:
            get_agent("invalid_agent")
        assert "sustainability" in str(exc_info.value)

    def test_list_agents_returns_dict_of_descriptions(self):
        from prompts.agents_config import list_agents
        agents = list_agents()
        assert isinstance(agents, dict)
        assert "sustainability" in agents
        assert isinstance(agents["sustainability"], str)
        assert len(agents["sustainability"]) > 0

    def test_sustainability_prompts_in_agents(self):
        from prompts.agents_config import AGENTS, SUSTAINABILITY_SYSTEM_PROMPT, SUSTAINABILITY_USER_PROMPT
        assert AGENTS["sustainability"]["system_prompt"] == SUSTAINABILITY_SYSTEM_PROMPT
        assert AGENTS["sustainability"]["user_prompt"] == SUSTAINABILITY_USER_PROMPT


# =============================================================================
# prompts/sustainability_agent.py
# =============================================================================

class TestSustainabilityAgent:
    """Covers prompts/sustainability_agent.py lines 9-28."""

    def test_get_system_prompt_returns_string(self):
        from prompts.sustainability_agent import get_system_prompt
        result = get_system_prompt()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_user_prompt_returns_string(self):
        from prompts.sustainability_agent import get_user_prompt
        result = get_user_prompt()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_tags_returns_list(self):
        from prompts.sustainability_agent import get_tags
        tags = get_tags()
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert "tampinhas" in tags

    def test_system_prompt_constant(self):
        from prompts.sustainability_agent import SYSTEM_PROMPT
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0

    def test_user_prompt_constant(self):
        from prompts.sustainability_agent import USER_PROMPT
        assert isinstance(USER_PROMPT, str)
        assert len(USER_PROMPT) > 0

    def test_tags_constant(self):
        from prompts.sustainability_agent import TAGS
        assert isinstance(TAGS, list)

    def test_get_system_prompt_equals_constant(self):
        from prompts.sustainability_agent import get_system_prompt, SYSTEM_PROMPT
        assert get_system_prompt() == SYSTEM_PROMPT

    def test_get_user_prompt_equals_constant(self):
        from prompts.sustainability_agent import get_user_prompt, USER_PROMPT
        assert get_user_prompt() == USER_PROMPT

    def test_get_tags_equals_constant(self):
        from prompts.sustainability_agent import get_tags, TAGS
        assert get_tags() == TAGS


# =============================================================================
# prompts/sustainability_config.py
# =============================================================================

class TestSustainabilityConfig:
    """Covers prompts/sustainability_config.py lines 9-55."""

    def test_openai_config_model(self):
        from prompts.sustainability_config import OPENAI_CONFIG
        assert OPENAI_CONFIG["model"] == "gpt-3.5-turbo"
        assert "temperature" in OPENAI_CONFIG
        assert "max_tokens" in OPENAI_CONFIG

    def test_metadata_version_and_language(self):
        from prompts.sustainability_config import METADATA
        assert METADATA["version"] == "2.0"
        assert METADATA["language"] == "pt-BR"
        assert "name" in METADATA
        assert "description" in METADATA

    def test_cache_config(self):
        from prompts.sustainability_config import CACHE_CONFIG
        assert CACHE_CONFIG["enabled"] is True
        assert CACHE_CONFIG["duration_seconds"] == 86400
        assert "storage" in CACHE_CONFIG

    def test_timeout_config(self):
        from prompts.sustainability_config import TIMEOUT_CONFIG
        assert "openai_request" in TIMEOUT_CONFIG
        assert "tts_synthesis" in TIMEOUT_CONFIG
        assert "total_generation" in TIMEOUT_CONFIG

    def test_retry_config(self):
        from prompts.sustainability_config import RETRY_CONFIG
        assert RETRY_CONFIG["max_attempts"] == 3
        assert RETRY_CONFIG["backoff_factor"] == 2
        assert "retry_on" in RETRY_CONFIG

    def test_logging_config(self):
        from prompts.sustainability_config import LOGGING_CONFIG
        assert LOGGING_CONFIG["level"] == "INFO"
        assert "format" in LOGGING_CONFIG
        assert "file" in LOGGING_CONFIG

    def test_fallback_config(self):
        from prompts.sustainability_config import FALLBACK_CONFIG
        assert FALLBACK_CONFIG["use_cached_audio"] is True
        assert FALLBACK_CONFIG["use_placeholder_audio"] is True
        assert "placeholder_duration" in FALLBACK_CONFIG


# =============================================================================
# prompts/sustainability_prompts.py
# =============================================================================

class TestSustainabilityPrompts:
    """Covers prompts/sustainability_prompts.py lines 9-27."""

    def test_system_prompt_is_string(self):
        from prompts.sustainability_prompts import SYSTEM_PROMPT
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0

    def test_script_texto_constant(self):
        from prompts.sustainability_prompts import SCRIPT_TEXTO
        assert isinstance(SCRIPT_TEXTO, str)
        assert "400 anos" in SCRIPT_TEXTO

    def test_user_prompt_equals_script_texto(self):
        from prompts.sustainability_prompts import USER_PROMPT, SCRIPT_TEXTO
        assert USER_PROMPT == SCRIPT_TEXTO

    def test_tags_list_contains_expected(self):
        from prompts.sustainability_prompts import TAGS
        assert isinstance(TAGS, list)
        assert "tampinhas" in TAGS
        assert "reciclagem" in TAGS
        assert len(TAGS) >= 5

    def test_tags_are_strings(self):
        from prompts.sustainability_prompts import TAGS
        for tag in TAGS:
            assert isinstance(tag, str)
