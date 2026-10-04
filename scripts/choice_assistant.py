"""English text CLI

English text HTTP English text APIEnglish text chat / archive / stats / decision / config-api English text
English textEnglish text

Skill English textEnglish text LLM API Key + English text API KeyiOS/MP English text
English textEnglish textEnglish textEnglish text config.py English text
  English text > SQLite > ~/.choice/config.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

# English text
DEFAULT_BASE_URL = "http://127.0.0.1:8010"

# English textEnglish text modes_data English text
MODES = ["auto", "rational", "random", "nature", "dialogue", "fengshui"]

# English textEnglish text services/config.py English text
CONFIG_PATH = Path.home() / ".choice" / "config.json"

# CLI flag -> English textEnglish text ChatRequest English text
# English text _collect_cli_config English text config English text
# v0.7.0 English text weather_keyEnglish text KeyEnglish textweather_appsecret English text
REQ_FIELD_MAP = {
    "llm_api_key": "apiKey",
    "llm_model": "llmModel",
    "llm_base_url": "llmBaseUrl",
    "weather_key": "weatherKey",
    "weather_base_url": "weatherBaseUrl",
    "weather_appsecret": "weatherAppsecret",  # English textEnglish text weather_key
    "weather_city": "weatherCity",
}


def _print_json(data: Any) -> None:
    """English text JSON"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _read_config_file() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config_file(partial: dict) -> dict:
    """English text ~/.choice/config.jsonEnglish text 0600"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(_read_config_file())
    for k, v in partial.items():
        if v is not None:
            merged[k] = v
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass
    return merged


def _collect_cli_config(args: argparse.Namespace) -> dict:
    """English text args English text CLI English textEnglish text

    v0.7.0 English text weather_keyEnglish text KeyEnglish text
    --weather-appsecret English textEnglish text weather_key
    """
    weather_key = getattr(args, "weather_key", None) or getattr(args, "weather_appsecret", None)
    return {
        "llm_api_key": getattr(args, "api_key", None),
        "llm_model": getattr(args, "llm_model", None),
        "llm_base_url": getattr(args, "llm_base_url", None),
        "weather_key": weather_key,
        "weather_base_url": getattr(args, "weather_base_url", None),
        "weather_appsecret": getattr(args, "weather_appsecret", None),
        "weather_city": getattr(args, "weather_city", None),
    }


def _build_request_overrides(cli_config: dict) -> dict:
    """English text CLI English text /api/chat English text"""
    return {REQ_FIELD_MAP[k]: v for k, v in cli_config.items() if v}


def cmd_chat(args: argparse.Namespace, client: httpx.Client) -> int:
    """English text /api/chatEnglish text"""
    if not args.question:
        print("English textchat English text --question English text", file=sys.stderr)
        return 2

    # --save-configEnglish text CLI English text ~/.choice/config.json
    if getattr(args, "save_config", False):
        cli_cfg = _collect_cli_config(args)
        if any(cli_cfg.values()):
            _save_config_file(cli_cfg)

    payload: dict = {"question": args.question, "mode": args.mode}
    payload.update(_build_request_overrides(_collect_cli_config(args)))
    resp = client.post("/api/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()

    # nature English text
    nature = data.get("nature")
    reply = data.get("reply", "")
    if reply:
        print(reply)
        print("-" * 48)

    if nature:
        _print_json(nature)
    else:
        _print_json(data.get("brief", {}))

    # English textEnglish text decisionIdEnglish text decision English text/English text
    decision_id = data.get("decisionId")
    if decision_id:
        print(f"English text id{decision_id}")
    return 0


def cmd_archive(args: argparse.Namespace, client: httpx.Client) -> int:
    """English text /api/archiveEnglish text

    English text { ok, list, total, page, pageSize }CLI English text list English text
    """
    resp = client.get("/api/archive")
    resp.raise_for_status()
    data = resp.json()
    items = data.get("list", []) if isinstance(data, dict) else data
    _print_json(items)
    return 0


def cmd_stats(args: argparse.Namespace, client: httpx.Client) -> int:
    """English text /api/statsEnglish text"""
    resp = client.get("/api/stats")
    resp.raise_for_status()
    _print_json(resp.json())
    return 0


def cmd_decision(args: argparse.Namespace, client: httpx.Client) -> int:
    """English text /api/decision/:idEnglish text"""
    if not args.id:
        print("English textdecision English text --id English text", file=sys.stderr)
        return 2

    if args.delete:
        resp = client.delete(f"/api/decision/{args.id}")
        resp.raise_for_status()
        print(f"English text {args.id}")
        return 0

    resp = client.get(f"/api/decision/{args.id}")
    resp.raise_for_status()
    _print_json(resp.json())
    return 0


def cmd_config_api(args: argparse.Namespace, client: httpx.Client) -> int:
    """English text /api/config English textEnglish text SQLite

    - English text / --listGET /api/config English text
    - --deleteDELETE /api/config English text API Key
    - --save-to-dbPOST /api/config English text CLI English text SQLite
    """
    # --save-to-db English text --delete English text --list
    if getattr(args, "save_to_db", False):
        cli_cfg = _collect_cli_config(args)
        if not any(cli_cfg.values()):
            print("English textconfig-api --save-to-db English text", file=sys.stderr)
            return 2
        # English text ConfigUpdate English text snake_caseEnglish text cli_cfg English text
        payload = {k: v for k, v in cli_cfg.items() if v}
        resp = client.post("/api/config", json=payload)
        resp.raise_for_status()
        print("English text SQLiteEnglish text")
        _print_json(resp.json())
        return 0

    if getattr(args, "delete", False):
        resp = client.delete("/api/config")
        resp.raise_for_status()
        print("English text SQLite English text API Key English text")
        return 0

    # English textGET /api/config
    resp = client.get("/api/config")
    resp.raise_for_status()
    _print_json(resp.json())
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """config English textEnglish text API Key"""
    cli_cfg = _collect_cli_config(args)

    # English text
    if not getattr(args, "save", False):
        current = dict(_read_config_file())
        for k, env in (
            ("llm_api_key", "CHOICE_LLM_API_KEY"),
            ("llm_model", "CHOICE_LLM_MODEL"),
            ("llm_base_url", "CHOICE_LLM_BASE_URL"),
            ("weather_key", "CHOICE_WEATHER_KEY"),
            ("weather_base_url", "CHOICE_WEATHER_BASE_URL"),
            ("weather_appsecret", "CHOICE_WEATHER_APPSECRET"),  # English text
            ("weather_city", "CHOICE_WEATHER_CITY"),
        ):
            env_val = os.environ.get(env)
            if env_val:
                current[k] = env_val
            elif cli_cfg.get(k):
                current[k] = cli_cfg[k]
        # English text secretEnglish text
        masked = dict(current)
        for k in ("llm_api_key", "weather_key", "weather_appsecret"):
            if masked.get(k):
                masked[k] = "***English text***"
        print(f"English text{CONFIG_PATH}")
        _print_json(masked)
        return 0

    if not any(cli_cfg.values()):
        print("English textconfig --save English text", file=sys.stderr)
        return 2

    merged = _save_config_file(cli_cfg)
    print(f"English text {CONFIG_PATH}English text 0600")
    masked = {k: ("***English text***" if v and k in ("llm_api_key", "weather_key", "weather_appsecret") else v)
              for k, v in merged.items()}
    _print_json(masked)
    return 0


def _add_config_flags(parser: argparse.ArgumentParser) -> None:
    """English text parser English text LLM / English text API Key English text

    v0.7.0 English textEnglish text --weather-key
    --weather-appsecret English textEnglish text weather_key
    English text Key English texthttps://lbs.amap.com/dev/key/app
    """
    parser.add_argument("--api-key", default=None, help="LLM API Key")
    parser.add_argument("--llm-model", default=None, help="LLM English textEnglish text gpt-4o-mini")
    parser.add_argument(
        "--llm-base-url", default=None,
        help="LLM base urlOpenAI English textEnglish text https://api.openai.com/v1 English text .../chat/completions",
    )
    parser.add_argument(
        "--weather-key", default=None,
        help="English text Key10 English text/English textEnglish texthttps://lbs.amap.com/dev/key/app",
    )
    parser.add_argument(
        "--weather-base-url", default=None,
        help="English textEnglish text https://restapi.amap.com/v3/weather/weatherInfo",
    )
    parser.add_argument(
        "--weather-appsecret", default=None,
        help="English textEnglish textEnglish text --weather-key",
    )
    parser.add_argument("--weather-city", default=None, help="English textEnglish text")


def build_parser() -> argparse.ArgumentParser:
    """English textchat / archive / stats / decision / config-api"""
    parser = argparse.ArgumentParser(
        prog="choice_assistant",
        description="English text CLI - English textEnglish text",
    )
    parser.add_argument("--question", "-q", help="English textchat English text")
    parser.add_argument(
        "--mode", "-m",
        default="auto",
        choices=MODES,
        help="English textEnglish text auto",
    )
    parser.add_argument(
        "--action", "-a",
        default="chat",
        choices=["chat", "archive", "stats", "decision", "config-api"],
        help="English textEnglish text chatdecision: English textEnglish text --idconfig-api: English text SQLite English text",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"English text API English textEnglish text {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="English text CLI English text ~/.choice/config.json",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="English text iddecision English text",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="English textdecision English textconfig-api English text SQLite English text API Key",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="English textconfig-api English textEnglish textEnglish text",
    )
    parser.add_argument(
        "--save-to-db",
        action="store_true",
        help="English text CLI English text SQLiteconfig-api English textEnglish text --api-key English text",
    )
    _add_config_flags(parser)
    return parser


def build_config_parser() -> argparse.ArgumentParser:
    """English text config English text"""
    parser = argparse.ArgumentParser(
        prog="choice_assistant config",
        description="English text API KeyEnglish text ~/.choice/config.jsonEnglish text 0600",
    )
    parser.add_argument("--save", action="store_true", help="English text")
    _add_config_flags(parser)
    return parser


def main() -> int:
    """English textEnglish text config English text chat/archive/stats English text"""
    argv = sys.argv[1:]
    # config English textpython choice_assistant.py config --api-key sk-xxx --save
    if argv and argv[0] == "config":
        args = build_config_parser().parse_args(argv[1:])
        return cmd_config(args)

    args = build_parser().parse_args(argv)
    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        if args.action == "chat":
            return cmd_chat(args, client)
        if args.action == "archive":
            return cmd_archive(args, client)
        if args.action == "stats":
            return cmd_stats(args, client)
        if args.action == "decision":
            return cmd_decision(args, client)
        if args.action == "config-api":
            return cmd_config_api(args, client)
    return 1


if __name__ == "__main__":
    sys.exit(main())
