#!/bin/sh
SCRIPT_DIR="/config/scripts"
MONITOR="$SCRIPT_DIR/spotify_monitor.py"
SUP_PIDFILE="$SCRIPT_DIR/.spotify_monitor_supervisor.pid"
SUP_LOCKDIR="$SCRIPT_DIR/.spotify_monitor_supervisor.lock"
LOG_DIR="/config/logs"
SUP_LOG="$LOG_DIR/spotify_monitor_supervisor.log"
ENV_FILE="$SCRIPT_DIR/spotify.env"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ -x "$VENV_DIR/bin/python3" ]; then
    PYTHON_BIN="$VENV_DIR/bin/python3"
else
    PYTHON_BIN="python3"
fi

mkdir -p "$LOG_DIR"

if ! mkdir "$SUP_LOCKDIR" 2>/dev/null; then
    echo "Spotify Monitor Supervisor: Start bereits aktiv, überspringe"
    exit 0
fi

cleanup_lock() {
    rmdir "$SUP_LOCKDIR" 2>/dev/null || true
}

trap cleanup_lock EXIT INT TERM

if [ -f "$SUP_PIDFILE" ]; then
    OLD_PID=$(cat "$SUP_PIDFILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Spotify Monitor Supervisor läuft bereits (PID $OLD_PID), überspringe Start"
        exit 0
    fi
    rm -f "$SUP_PIDFILE"
fi

# Extra-Check: Gibt es bereits einen laufenden Monitor-Python-Prozess?
# Verhindert Duplikate durch manuell gestartete Supervisoren ohne PID-Datei.
EXISTING_MONITOR_PID=$(pgrep -f "python.*spotify_monitor\.py" 2>/dev/null | head -1)
if [ -n "$EXISTING_MONITOR_PID" ]; then
    echo "Warnung: Monitor-Prozess bereits aktiv (PID $EXISTING_MONITOR_PID), beende alte Instanz"
    kill "$EXISTING_MONITOR_PID" 2>/dev/null
    sleep 2
    kill -9 "$EXISTING_MONITOR_PID" 2>/dev/null || true
fi

# Extra-Check: Gibt es einen laufenden Supervisor sh-Prozess?
EXISTING_SUP_PID=$(pgrep -f "while.*spotify_monitor" 2>/dev/null | head -1)
if [ -n "$EXISTING_SUP_PID" ] && [ "$EXISTING_SUP_PID" != "$$" ]; then
    echo "Warnung: Supervisor-Prozess bereits aktiv (PID $EXISTING_SUP_PID), beende"
    kill "$EXISTING_SUP_PID" 2>/dev/null
    sleep 1
fi

if [ ! -f "$MONITOR" ]; then
    echo "Fehler: $MONITOR nicht gefunden"
    exit 1
fi

if [ -f "$ENV_FILE" ]; then
    set -a
    . "$ENV_FILE"
    set +a
fi

setsid sh -c '
while true; do
    echo "$(date +"%Y-%m-%d %H:%M:%S") supervisor: start spotify_monitor.py" >> "'$SUP_LOG'"
    "'$PYTHON_BIN'" -u "'$MONITOR'" >> "'$SUP_LOG'" 2>&1
    EXIT_CODE=$?
    echo "$(date +"%Y-%m-%d %H:%M:%S") supervisor: monitor exited (code=$EXIT_CODE), restart in 3s" >> "'$SUP_LOG'"
    sleep 3
done
' </dev/null >/dev/null 2>&1 &

echo $! > "$SUP_PIDFILE"
echo "Spotify Monitor Supervisor gestartet (PID $(cat "$SUP_PIDFILE"))"
