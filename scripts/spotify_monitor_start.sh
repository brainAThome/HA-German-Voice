#!/bin/sh
# Starter für spotify_monitor.py
# Wird von HA shell_command aufgerufen.
# Startet den Monitor als Background-Daemon und kehrt sofort zurück.

SCRIPT="/config/scripts/spotify_monitor.py"
PIDFILE="/config/scripts/.spotify_monitor.pid"

# Alte Instanz beenden falls vorhanden
if [ -f "$PIDFILE" ]; then
    OLDPID=$(cat "$PIDFILE" 2>/dev/null)
    if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
        kill "$OLDPID" 2>/dev/null
        sleep 1
    fi
    rm -f "$PIDFILE"
fi

# Monitor im Hintergrund starten (setsid = neue Session, überlebt HA)
setsid python3 -u "$SCRIPT" </dev/null >/dev/null 2>&1 &

echo "Monitor gestartet (PID $!)"
