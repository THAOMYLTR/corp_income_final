"""build_llm names exactly what is missing, before any call is made; the
pre-run check reports the real cause of a failed call.

    python -m unittest testing.test_config
"""

import os
import sys
import types
import unittest
from unittest import mock

from src.config import build_llm, llm_provider
from src.llm_check import check_llm_setup
from src.llm_errors import explain_llm_error


class _Recorder:
    """Stands in for ChatOpenAI / ChatAnthropic and keeps its kwargs."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs


def _fake_modules():
    httpx = types.ModuleType("httpx")
    httpx.Client = lambda **kw: ("client", kw)
    httpx.URL = str
    httpx.Request = object
    return {
        "langchain_openai": types.SimpleNamespace(ChatOpenAI=_Recorder),
        "langchain_anthropic": types.SimpleNamespace(ChatAnthropic=_Recorder),
        "httpx": httpx,
    }


class BuildLlmTest(unittest.TestCase):
    def build(self, env, *args, **kwargs):
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.dict(sys.modules, _fake_modules()):
            return build_llm(*args, **kwargs)

    def test_unset_model_variable_is_named(self):
        with self.assertRaisesRegex(ValueError, r"MODEL_ECONOMY is not set.*\.env\.example"):
            self.build({}, "MODEL_ECONOMY")

    def test_missing_key_is_named_per_provider(self):
        for provider, needed in (("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY"),
                                 ("databricks", "DATABRICKS_HOST"),
                                 ("databricks_invocations", "ANTHROPIC_API_BASE")):
            with self.subTest(provider=provider):
                with self.assertRaisesRegex(ValueError, needed):
                    self.build({"MODEL_ECONOMY": "m", "LLM_PROVIDER": provider}, "MODEL_ECONOMY")

    def test_unknown_provider_is_refused(self):
        with self.assertRaisesRegex(ValueError, "LLM_PROVIDER"):
            self.build({"MODEL_ECONOMY": "m", "LLM_PROVIDER": "gemini"}, "MODEL_ECONOMY")

    def test_openai_key_from_environment(self):
        llm = self.build({"MODEL_DOCUMENT": "gpt-4o-mini", "OPENAI_API_KEY": "sk-env"}, "MODEL_DOCUMENT")
        self.assertEqual(llm.kwargs["api_key"], "sk-env")
        self.assertIsNone(llm.kwargs["base_url"])          # api.openai.com
        self.assertEqual(llm.kwargs["model"], "gpt-4o-mini")

    def test_api_key_argument_wins_and_counts_as_present(self):
        llm = self.build({"MODEL_DOCUMENT": "gpt-4o"}, "MODEL_DOCUMENT", api_key="sk-arg")
        self.assertEqual(llm.kwargs["api_key"], "sk-arg")

    def test_team_databricks_convention_when_api_base_is_set(self):
        env = {"MODEL_PREMIUM": "claude-endpoint", "OPENAI_API_KEY": "dapi123",
               "ANTHROPIC_API_BASE": "https://x.cloud.databricks.com/serving-endpoints/"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(llm_provider(), "databricks_invocations")
        llm = self.build(env, "MODEL_PREMIUM", thinking_budget=2000)
        self.assertEqual(llm.kwargs["base_url"],
                         "https://x.cloud.databricks.com/serving-endpoints/claude-endpoint")
        self.assertIn("http_client", llm.kwargs)
        self.assertEqual(llm.kwargs["model_kwargs"]["thinking"]["budget_tokens"], 2000)

    def test_team_convention_accepts_the_databricks_token_variable(self):
        env = {"MODEL_PREMIUM": "ep", "ANTHROPIC_API_BASE": "https://x/serving-endpoints",
               "DATABRICKS_API_TOKEN": "dapi-abc"}
        self.assertEqual(self.build(env, "MODEL_PREMIUM").kwargs["api_key"], "dapi-abc")

    def test_thinking_budget_is_ignored_by_openai(self):
        llm = self.build({"MODEL_DOCUMENT": "gpt-4o", "OPENAI_API_KEY": "sk"}, "MODEL_DOCUMENT",
                         temperature=0.0, thinking_budget=2000)
        self.assertEqual(llm.kwargs["temperature"], 0.0)
        self.assertNotIn("model_kwargs", llm.kwargs)


class ExplainErrorTest(unittest.TestCase):
    def test_root_cause_and_hint_behind_connection_error(self):
        class APIConnectionError(Exception):
            pass

        try:
            try:
                raise OSError("[Errno -2] Name or service not known")
            except OSError as inner:
                raise APIConnectionError("Connection error.") from inner
        except APIConnectionError as exc:
            text = explain_llm_error(exc)
        self.assertIn("APIConnectionError: Connection error.", text)
        self.assertIn("nguyên nhân gốc: OSError", text)
        self.assertIn("tên miền", text)

    def test_missing_credentials_hint(self):
        text = explain_llm_error(Exception("Missing credentials. Please pass an `api_key`"))
        self.assertIn("OPENAI_API_KEY", text)


class _Llm:
    def __init__(self, model, fail=None):
        self.model_name, self.fail, self.calls = model, fail, 0

    def invoke(self, _):
        self.calls += 1
        if self.fail:
            raise self.fail
        return types.SimpleNamespace(content="OK")


class CheckLlmSetupTest(unittest.TestCase):
    def config(self, **llms):
        fields = ("document_llm", "legal_basic_extraction_llm", "shareholders_extraction_llm",
                  "legal_rep_extraction_llm", "liabilities_extraction_llm")
        return types.SimpleNamespace(**{f: llms.get(f) for f in fields})

    def test_each_model_called_once_and_success_passes(self):
        mini, big = _Llm("gpt-4o-mini"), _Llm("gpt-4o")
        cfg = self.config(document_llm=mini, legal_rep_extraction_llm=mini,
                          legal_basic_extraction_llm=big)
        with mock.patch("builtins.print"):
            self.assertTrue(check_llm_setup(cfg))
        self.assertEqual((mini.calls, big.calls), (1, 1))

    def test_failure_stops_the_run_with_the_cause(self):
        cfg = self.config(document_llm=_Llm("gpt-4o", fail=Exception("Error code: 401 invalid_api_key")))
        with mock.patch("builtins.print") as printed:
            with self.assertRaises(RuntimeError):
                check_llm_setup(cfg)
        output = " ".join(str(c.args[0]) for c in printed.call_args_list if c.args)
        self.assertIn("Key sai", output)

    def test_secrets_are_masked(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-proj-SECRET-1234567"}, clear=True), \
                mock.patch("builtins.print") as printed:
            check_llm_setup(None)
        output = " ".join(str(c.args[0]) for c in printed.call_args_list if c.args)
        self.assertNotIn("SECRET", output)


if __name__ == "__main__":
    unittest.main()
