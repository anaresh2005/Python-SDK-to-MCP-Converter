import sys, json
from registry import build_registry
from executor import call_tool


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python cli.py <tool_name> '<json-payload>'\nExample: python cli.py gh_get_user '{\"login\":\"octocat\"}'"
        )
        sys.exit(1)

    tool_name = sys.argv[1]
    try:
        payload = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(f"Invalid JSON payload: {e}")
        sys.exit(2)

    reg = build_registry("config/github.yaml")
    ms = reg.get(tool_name)
    if not ms:
        print(f"Unknown tool: {tool_name}. Available: {', '.join(reg)}")
        sys.exit(3)

    out = call_tool(ms, payload)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
