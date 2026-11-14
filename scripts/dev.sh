#!/usr/bin/env bash
# Desktop -> Pi dev loop: copy the working copy to the Pi and run it there.
#
# Interactive (block until Ctrl+C):
#   scripts/dev.sh            copy, restart service, follow log
#                             (Ctrl+C stops following; the camera keeps running)
#   scripts/dev.sh --fg       copy, stop service, run in this terminal
#                             (Ctrl+C stops the camera; service restarts on exit)
#   scripts/dev.sh --logs     follow the log only
#   scripts/dev.sh --clean    list files on the Pi that are not in the working copy
#                             (e.g. deleted locally) and delete them after a y/N prompt;
#                             never touches DCIM/ or .git/. Without a terminal: list only.
#
# Non-interactive (exit 0 = OK, 1 = FAIL; safe for Claude and scripts):
#   scripts/dev.sh --check    copy, restart, wait for "Camera initialized" (max 20 s); FAIL on
#                             traceback/error or if the service is not running
#   scripts/dev.sh --test     copy, run pytest on the Pi
#   scripts/dev.sh --shoot    trigger the web shutter on the running service, wait for
#                             JPG + DNG + thumbnail, print sizes, copy JPG + thumbnail
#                             to device-out/; FAIL if a file is missing or the log has errors
#   scripts/dev.sh --health   print service, picamera2 version, OS, memory, disk,
#                             throttling, console blanking, groups
#
# One-time:
#   scripts/dev.sh --install  install and enable the systemd service
#
# Config (environment):
#   PI_HOST  ssh host or alias            (default: pi)
#   PI_DIR   project path, relative to the Pi user's home (default: workspace/pi-camera)
#
# Requires SSH key login and passwordless sudo for systemctl/journalctl on the Pi.
set -euo pipefail

PI_HOST="${PI_HOST:-pi}"
PI_DIR="${PI_DIR:-workspace/pi-camera}"
SERVICE=pi-camera
OUT_DIR=device-out

cd "$(dirname "$0")/.."

remote() { ssh "$PI_HOST" "$@"; }

# Files that belong on the Pi, NUL-separated: tracked + untracked-but-not-ignored
# (DCIM/ and __pycache__ are git-ignored), minus desktop-only folders, existing on disk.
local_files() {
  git ls-files -co --exclude-standard -z \
    | grep -zvE '^(\.claude/|audits/|docs/|scripts/)|\.psd$' \
    | while IFS= read -r -d '' f; do if [ -e "$f" ]; then printf '%s\0' "$f"; fi; done
}

sync_files() {
  echo "-> copying working copy to $PI_HOST:~/$PI_DIR"
  remote "mkdir -p '$PI_DIR'"
  # Files deleted locally are NOT deleted on the Pi; see --clean.
  local_files | tar --null -cf - -T - | remote "tar -xf - -C '$PI_DIR'"
}

# Regular files on the Pi that are not in local_files. Never lists DCIM/, .git/ or __pycache__/.
stale_files() {
  local_files | tr '\0' '\n' | remote "cd '$PI_DIR' && l=\$(mktemp) && sort > \"\$l\" &&
    find . -type f ! -path './DCIM/*' ! -path './.git/*' ! -path '*/__pycache__/*' \
      | sed 's|^\./||' | sort | comm -23 - \"\$l\"; rm -f \"\$l\""
}

restart() {
  echo "-> restarting $SERVICE"
  remote "sudo systemctl restart $SERVICE"
}

follow_logs() {
  ssh -t "$PI_HOST" "sudo journalctl -fu $SERVICE -n 20 -o cat"
}

remote_now() { remote "date '+%Y-%m-%d %H:%M:%S'"; }

log_since() { remote "sudo journalctl -u $SERVICE --since '$1' --no-pager -o cat"; }

# Output of the current service run only (not the previous run's shutdown).
log_current_run() {
  remote "sudo journalctl _SYSTEMD_INVOCATION_ID=\$(systemctl show -p InvocationID --value $SERVICE) --no-pager -o cat"
}

fail_on_errors() {
  if grep -qiE 'traceback|error' <<<"$1"; then  # -i: libcamera logs "ERROR"
    echo "FAIL: errors in log"; exit 1
  fi
}

case "${1:-}" in
  "")
    sync_files
    restart
    follow_logs
    ;;
  --fg)
    sync_files
    echo "-> stopping $SERVICE, running in foreground (Ctrl+C to stop)"
    remote "sudo systemctl stop $SERVICE" || true
    trap 'echo "-> starting $SERVICE again"; remote "sudo systemctl start $SERVICE"' EXIT
    ssh -t "$PI_HOST" "cd '$PI_DIR' && python3 main.py" || true
    ;;
  --logs)
    follow_logs
    ;;
  --check)
    sync_files
    restart
    echo "-> waiting for camera startup (max 20 s)"
    remote "for i in \$(seq 40); do
        sudo journalctl _SYSTEMD_INVOCATION_ID=\$(systemctl show -p InvocationID --value $SERVICE) --no-pager -o cat \
          | grep -qE 'Camera initialized|Traceback' && exit 0
        sleep 0.5
      done; exit 0"
    log="$(log_current_run)"
    echo "$log"
    if ! remote "systemctl is-active --quiet $SERVICE"; then
      echo "FAIL: $SERVICE is not running"; exit 1
    fi
    fail_on_errors "$log"
    if ! grep -q 'Camera initialized' <<<"$log"; then
      echo "FAIL: camera did not initialize within 20 s"; exit 1
    fi
    echo "OK: $SERVICE running, camera initialized, no errors since restart"
    ;;
  --test)
    sync_files
    echo "-> running pytest on the Pi"
    remote "cd '$PI_DIR' && python3 -m pytest -q -p no:cacheprovider tests"
    ;;
  --shoot)
    since="$(remote_now)"
    echo "-> triggering shutter"
    # Wait (max 30 s) for the camera's "Photo saved" line for a new JPG: JPG and DNG are then complete.
    name="$(remote "cd '$PI_DIR/DCIM' || exit 1
      before=\$(ls -1t *.jpg 2>/dev/null | head -1)
      t0=\$(date +%s)
      curl -fsS -X POST http://localhost:5000/api/trigger >/dev/null || exit 1
      for i in \$(seq 60); do
        sleep 0.5
        new=\$(ls -1t *.jpg 2>/dev/null | head -1)
        log=\$(sudo journalctl -u $SERVICE --since '$since' -o cat)
        echo \"\$log\" | grep -q 'Error capturing photo' && exit 1
        if [ -n \"\$new\" ] && [ \"\$new\" != \"\$before\" ] && echo \"\$log\" | grep -q \"Photo saved: \$new\"; then
          echo \"trigger to saved: <= \$((\$(date +%s) - t0 + 1)) s (log has exact times)\" >&2; echo \"\$new\"; exit 0
        fi
      done
      exit 1")" || { echo "FAIL: capture error or no new photo within 30 s"; log_since "$since"; exit 1; }
    stem="${name%.jpg}"
    echo "-> captured $stem"
    # Thumbnails are made on first request, like the gallery does
    remote "curl -fsS -o /dev/null http://localhost:5000/dcim/thumbs/$name" || { echo "FAIL: thumbnail request"; exit 1; }
    remote "cd '$PI_DIR/DCIM' && ls -l '$name' '$stem.dng' 'thumbs/$name' 2>&1
      python3 -c \"from PIL import Image; print('jpg size:', Image.open('$name').size); print('thumb size:', Image.open('thumbs/$name').size)\""
    mkdir -p "$OUT_DIR"
    scp -q "$PI_HOST:$PI_DIR/DCIM/$name" "$OUT_DIR/$name"
    scp -q "$PI_HOST:$PI_DIR/DCIM/thumbs/$name" "$OUT_DIR/thumb_$name"
    echo "-> copied to $OUT_DIR/$name and $OUT_DIR/thumb_$name"
    log="$(log_since "$since")"
    echo "$log"
    remote "test -e '$PI_DIR/DCIM/$stem.dng'" || { echo "FAIL: DNG missing"; exit 1; }
    fail_on_errors "$log"
    echo "OK: JPG, DNG and thumbnail written"
    ;;
  --health)
    remote "
      echo '== service';      systemctl is-enabled $SERVICE; systemctl is-active $SERVICE
      echo '== picamera2';    dpkg-query -W -f='\${Version}\n' python3-picamera2
      echo '== python';       python3 --version
      echo '== os';           . /etc/os-release; echo \"\$PRETTY_NAME\"; uname -r
      echo '== memory (MB)';  free -m
      echo '== disk';         df -h ~
      echo '== photos';       ls '$PI_DIR/DCIM'/*.jpg 2>/dev/null | wc -l
      echo '== throttled (0x0 = ok)'; vcgencmd get_throttled 2>&1
      echo '== consoleblank (0 = never blank)'; cat /sys/module/kernel/parameters/consoleblank
      echo '== groups';       id -nG
      echo '== camera this boot'
      sudo journalctl -u $SERVICE -b --no-pager -o cat | grep -m3 -E 'Camera initialized|Error|Traceback' || echo 'no camera line this boot'
    "
    ;;
  --clean)
    stale="$(stale_files)"
    if [ -z "$stale" ]; then
      echo "OK: nothing to clean on $PI_HOST:~/$PI_DIR"; exit 0
    fi
    echo "Files on $PI_HOST:~/$PI_DIR that are not in the working copy:"
    sed 's/^/  /' <<<"$stale"
    if [ ! -t 0 ]; then
      echo "(no terminal: listed only, nothing deleted)"; exit 0
    fi
    read -r -p "Delete these $(wc -l <<<"$stale") file(s) on the Pi? [y/N] " answer
    [ "$answer" = "y" ] || { echo "Nothing deleted."; exit 0; }
    # Re-check every path on the Pi side: relative, no '..', never DCIM/ or .git/.
    remote "cd '$PI_DIR' && while IFS= read -r f; do
        case \"\$f\" in ''|/*|*..*|DCIM/*|.git/*) echo \"skipped: \$f\"; continue;; esac
        rm -f -- \"\$f\" && echo \"deleted: \$f\"
      done" <<<"$stale"
    ;;
  --install)
    sync_files
    ssh -t "$PI_HOST" "set -e
      dir=\$(cd '$PI_DIR' && pwd); user=\$(id -un)
      sed -e 's/\r\$//' -e \"s|__DIR__|\$dir|g\" -e \"s|__USER__|\$user|g\" \"\$dir/deploy/$SERVICE.service\" \
        | sudo tee /etc/systemd/system/$SERVICE.service >/dev/null
      sudo systemctl daemon-reload
      sudo systemctl enable --now $SERVICE
      systemctl status --no-pager $SERVICE"
    ;;
  *)
    sed -n '2,31p' "$0"; exit 2
    ;;
esac
