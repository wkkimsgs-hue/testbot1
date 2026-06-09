#!/data/data/com.termux/files/usr/bin/bash
MUSL_BIN="/data/data/com.termux/files/usr/lib/node_modules/@anthropic-ai/claude-code-linux-arm64-musl/claude"
HOME_DIR="/data/data/com.termux/files/home"

exec proot-distro login alpine --user claude --bind "$HOME_DIR:/home/claude" -- \
  sh -c 'cd /home/claude/test1 && exec "$0" --dangerously-skip-permissions "$@"' \
  "$MUSL_BIN" "$@"
