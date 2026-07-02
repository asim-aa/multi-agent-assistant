from multi_agent_assistant.tools.time_tools import get_current_time


def test_get_current_time_bangalore():
    result = get_current_time("Bangalore, India")

    result_text = str(result).lower()

    assert "asia/kolkata" in result_text
    assert "bangalore" in result_text or "india" in result_text


def test_get_current_time_tokyo():
    result = get_current_time("Tokyo, Japan")

    result_text = str(result).lower()

    assert "asia/tokyo" in result_text
    assert "tokyo" in result_text or "japan" in result_text
