"""Tests for the public headless API (tool_eval_bench.api) and schema module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tool_eval_bench.api import (
    ARGS_SCHEMA,
    OUTPUT_SCHEMA_VERSION,
    format_result,
    run_benchmark,
)
from tool_eval_bench.schema import ARGS_SCHEMA as SCHEMA_DIRECT, get_schema


# ---------------------------------------------------------------------------
# format_result tests
# ---------------------------------------------------------------------------

class TestFormatResult:
    """Test the versioned envelope wrapper."""

    def test_adds_schema_version(self):
        data = {"run_id": "test-123", "scores": {}}
        result = format_result(data)
        assert result["schema_version"] == OUTPUT_SCHEMA_VERSION

    def test_adds_tool_version(self):
        from tool_eval_bench import __version__

        data = {"run_id": "test-123", "scores": {}}
        result = format_result(data)
        assert result["tool_eval_bench_version"] == __version__

    def test_preserves_run_data(self):
        data = {
            "run_id": "test-123",
            "status": "completed",
            "config": {"model": "qwen"},
            "scores": {"final_score": 87, "max_points": 138},
        }
        result = format_result(data)
        assert result["run_id"] == "test-123"
        assert result["status"] == "completed"
        assert result["config"]["model"] == "qwen"

    def test_promotes_spark_arena_fields(self):
        data = {
            "run_id": "test-123",
            "scores": {
                "final_score": 87,
                "rating": "★★★★ Good",
                "safety_warnings": ["TC-K1 failed"],
                "deployability": 82,
                "responsiveness": 72,
                "max_points": 138,
            },
        }
        result = format_result(data)
        assert result["final_score"] == 87
        assert result["rating"] == "★★★★ Good"
        assert result["safety_warnings"] == ["TC-K1 failed"]
        assert result["deployability"] == 82
        assert result["responsiveness"] == 72
        assert result["total_scenarios"] == 69  # 138 / 2

    def test_empty_scores_returns_none_fields(self):
        result = format_result({"scores": {}})
        assert result["final_score"] is None
        assert result["rating"] is None
        assert result["safety_warnings"] == []
        assert result["total_scenarios"] is None

    def test_json_serializable(self):
        data = {
            "run_id": "test-123",
            "scores": {"final_score": 87, "max_points": 138},
        }
        result = format_result(data)
        text = json.dumps(result)
        assert "schema_version" in text


# ---------------------------------------------------------------------------
# ARGS_SCHEMA tests
# ---------------------------------------------------------------------------

class TestArgsSchema:
    """Test the machine-readable argument schema."""

    def test_schema_is_list(self):
        assert isinstance(ARGS_SCHEMA, list)

    def test_schema_not_empty(self):
        assert len(ARGS_SCHEMA) > 10  # we have ~20+ args

    def test_all_entries_have_required_fields(self):
        for entry in ARGS_SCHEMA:
            assert "name" in entry, f"Missing 'name' in {entry}"
            assert "type" in entry, f"Missing 'type' in {entry}"
            assert "description" in entry, f"Missing 'description' in {entry}"
            # default can be None, so just check key exists
            assert "default" in entry, f"Missing 'default' in {entry}"

    def test_known_args_present(self):
        names = {e["name"] for e in ARGS_SCHEMA}
        assert "backend" in names
        assert "temperature" in names
        assert "short" in names
        assert "hardmode" in names
        assert "timeout" in names
        assert "parallel" in names
        assert "alpha" in names

    def test_re_export_matches(self):
        """ARGS_SCHEMA from api.py should be the same object as from schema.py."""
        assert ARGS_SCHEMA is SCHEMA_DIRECT

    def test_get_schema_includes_version(self):
        schema = get_schema()
        assert "schema_version" in schema
        assert "args" in schema
        assert schema["args"] is ARGS_SCHEMA


# ---------------------------------------------------------------------------
# run_benchmark tests (mocked service)
# ---------------------------------------------------------------------------

class TestRunBenchmark:
    """Test the programmatic run_benchmark entry point."""

    @pytest.fixture()
    def mock_service(self):
        """Create a mock BenchmarkService that returns a fake run_data."""
        service = MagicMock()
        service.run_benchmark = AsyncMock(return_value={
            "run_id": "mock-run",
            "status": "completed",
            "config": {"model": "test-model"},
            "scores": {
                "final_score": 100,
                "max_points": 30,
                "rating": "★★★★★ Excellent",
            },
            "metadata": {},
        })
        return service

    @pytest.mark.asyncio
    async def test_returns_versioned_envelope(self, mock_service):
        with patch(
            "tool_eval_bench.api.BenchmarkService", return_value=mock_service
        ):
            result = await run_benchmark(
                model="test-model",
                base_url="http://localhost:8000",
                persist=False,
            )
        assert result["schema_version"] == OUTPUT_SCHEMA_VERSION
        assert result["run_id"] == "mock-run"
        assert result["final_score"] == 100

    @pytest.mark.asyncio
    async def test_short_flag_uses_core_scenarios(self, mock_service):
        from tool_eval_bench.evals.scenarios import SCENARIOS

        with patch(
            "tool_eval_bench.api.BenchmarkService", return_value=mock_service
        ):
            await run_benchmark(
                model="test-model",
                base_url="http://localhost:8000",
                short=True,
                persist=False,
            )
        call_kwargs = mock_service.run_benchmark.call_args.kwargs
        assert len(call_kwargs["scenarios"]) == len(SCENARIOS)

    @pytest.mark.asyncio
    async def test_persist_false_skips_storage(self, mock_service):
        with patch(
            "tool_eval_bench.api.BenchmarkService", return_value=mock_service
        ) as mock_cls:
            await run_benchmark(
                model="test-model",
                base_url="http://localhost:8000",
                persist=False,
            )
        # When persist=False, service is constructed with repo=None, reporter=None
        mock_cls.assert_called_once_with(repo=None, reporter=None)

    @pytest.mark.asyncio
    async def test_callbacks_forwarded(self, mock_service):
        start_cb = AsyncMock()
        result_cb = AsyncMock()
        with patch(
            "tool_eval_bench.api.BenchmarkService", return_value=mock_service
        ):
            await run_benchmark(
                model="test-model",
                base_url="http://localhost:8000",
                on_scenario_start=start_cb,
                on_scenario_result=result_cb,
                persist=False,
            )
        call_kwargs = mock_service.run_benchmark.call_args.kwargs
        assert call_kwargs["on_scenario_start"] is start_cb
        assert call_kwargs["on_scenario_result"] is result_cb


# ---------------------------------------------------------------------------
# JSONL progress callbacks (from cli/bench.py)
# ---------------------------------------------------------------------------

class TestStderrProgress:
    """Test the JSONL progress event callbacks."""

    @pytest.mark.asyncio
    async def test_scenario_start_emits_jsonl(self, capsys):
        from tool_eval_bench.cli.bench import _stderr_progress_start

        scenario = MagicMock()
        scenario.id = "TC-01"
        scenario.title = "Test Scenario"
        scenario.category.value = "A"

        await _stderr_progress_start(scenario, 0, 69)

        captured = capsys.readouterr()
        line = captured.err.strip()
        event = json.loads(line)
        assert event["event"] == "scenario_start"
        assert event["scenario_id"] == "TC-01"
        assert event["index"] == 0
        assert event["total"] == 69

    @pytest.mark.asyncio
    async def test_scenario_result_emits_jsonl(self, capsys):
        from tool_eval_bench.cli.bench import _stderr_progress_result

        scenario = MagicMock()
        scenario.id = "TC-01"

        result = MagicMock()
        result.status.value = "pass"
        result.points = 2
        result.duration_seconds = 1.234

        await _stderr_progress_result(scenario, result, 0, 69)

        captured = capsys.readouterr()
        line = captured.err.strip()
        event = json.loads(line)
        assert event["event"] == "scenario_result"
        assert event["scenario_id"] == "TC-01"
        assert event["status"] == "pass"
        assert event["points"] == 2
        assert event["duration_seconds"] == 1.23


# ---------------------------------------------------------------------------
# _emit_json_output tests
# ---------------------------------------------------------------------------

class TestEmitJsonOutput:
    """Test JSON output to stdout and file."""

    def test_stdout_output(self, capsys):
        from tool_eval_bench.cli.bench import _emit_json_output

        data = {"run_id": "test", "scores": {"final_score": 50}}
        _emit_json_output(data)

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["schema_version"] == OUTPUT_SCHEMA_VERSION
        assert parsed["run_id"] == "test"

    def test_file_output(self, tmp_path, capsys):
        from tool_eval_bench.cli.bench import _emit_json_output

        out_file = str(tmp_path / "result.json")
        data = {"run_id": "file-test", "scores": {"final_score": 75}}
        _emit_json_output(data, json_file=out_file)

        # Should NOT print to stdout
        captured = capsys.readouterr()
        assert captured.out == ""

        # Should write to file
        content = json.loads(Path(out_file).read_text())
        assert content["run_id"] == "file-test"
        assert content["schema_version"] == OUTPUT_SCHEMA_VERSION

        # Should emit benchmark_complete on stderr
        stderr_line = captured.err.strip()
        event = json.loads(stderr_line)
        assert event["event"] == "benchmark_complete"
        assert event["json_file"] == out_file

    def test_file_creates_parent_dirs(self, tmp_path):
        from tool_eval_bench.cli.bench import _emit_json_output

        out_file = str(tmp_path / "nested" / "deep" / "result.json")
        _emit_json_output({"scores": {}}, json_file=out_file)
        assert Path(out_file).exists()


# ---------------------------------------------------------------------------
# Headless model detection (P0 agent-friendliness)
# ---------------------------------------------------------------------------

class TestHeadlessModelDetection:
    """Test that --json mode auto-selects models without interactive prompts."""

    def test_headless_auto_selects_first_model(self, capsys):
        """When headless=True and multiple models are available, pick the first."""
        from io import StringIO

        from rich.console import Console

        from tool_eval_bench.cli.bench import _detect_model

        # Mock httpx response with 2 models
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "model-a", "root": "org/model-a"},
                {"id": "model-b", "root": "org/model-b"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        console = Console(file=StringIO(), width=200, no_color=True)

        with patch("tool_eval_bench.cli.bench.asyncio") as mock_asyncio:
            mock_asyncio.run.return_value = (mock_response, False)
            api_id, display = _detect_model(
                "http://localhost:8000", None, console,
                headless=True,
            )

        assert api_id == "model-a"
        assert display == "org/model-a"

        # Should emit JSONL event on stderr
        captured = capsys.readouterr()
        event = json.loads(captured.err.strip())
        assert event["event"] == "model_auto_selected"
        assert event["model"] == "model-a"
        assert event["total_available"] == 2
        assert "model-b" in event["available_models"]

    def test_headless_single_model_no_event(self, capsys):
        """Single model should auto-select without emitting model_auto_selected."""
        from io import StringIO

        from rich.console import Console

        from tool_eval_bench.cli.bench import _detect_model

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "only-model"}]
        }
        mock_response.raise_for_status = MagicMock()

        console = Console(file=StringIO(), width=200, no_color=True)

        with patch("tool_eval_bench.cli.bench.asyncio") as mock_asyncio:
            mock_asyncio.run.return_value = (mock_response, False)
            api_id, display = _detect_model(
                "http://localhost:8000", None, console,
                headless=True,
            )

        assert api_id == "only-model"
        # No model_auto_selected event for single model
        captured = capsys.readouterr()
        assert captured.err.strip() == ""


class TestHeadlessError:
    """Test structured error output for headless mode."""

    def test_emits_jsonl_and_exits(self, capsys):
        from tool_eval_bench.cli.bench import _headless_error

        with pytest.raises(SystemExit) as exc_info:
            _headless_error("connection_failed", "Server is down", exit_code=2)

        assert exc_info.value.code == 2

        captured = capsys.readouterr()
        event = json.loads(captured.err.strip())
        assert event["event"] == "error"
        assert event["error"] == "connection_failed"
        assert event["message"] == "Server is down"

    def test_exit_code_3_for_no_models(self, capsys):
        from tool_eval_bench.cli.bench import _headless_error

        with pytest.raises(SystemExit) as exc_info:
            _headless_error("no_models", "Empty model list", exit_code=3)

        assert exc_info.value.code == 3

    def test_default_exit_code_is_1(self, capsys):
        from tool_eval_bench.cli.bench import _headless_error

        with pytest.raises(SystemExit) as exc_info:
            _headless_error("unknown", "Something broke")

        assert exc_info.value.code == 1
