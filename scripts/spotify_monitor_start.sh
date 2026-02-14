#!/bin/sh
SUPERVISOR="/config/scripts/spotify_monitor_supervisor.sh"

if [ ! -x "$SUPERVISOR" ]; then
    echo "Fehler: $SUPERVISOR nicht gefunden oder nicht ausführbar"
    exit 1
fi

exec "$SUPERVISOR"
