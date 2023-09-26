{{ define "lunchables.localinstall" -}}
#!/bin/sh

TERMINAL_EMULATOR="gnome-terminal --"

cat >~/.local/bin/lunch-adm <<EOF
#!/bin/sh
{{ include "lunchables.localenv" . }}

pgrep lunch-portfwd >/dev/null || $TERMINAL_EMULATOR lunch-portfwd
exec ~/.local/share/lunchables/env/bin/python "\${LUNCHABLES_LEADER-\$HOME/.local/share/lunchables/leader.py}" "\$@"
EOF
chmod +x ~/.local/bin/lunch-adm

cat >~/.local/bin/lunch-portfwd <<EOF
{{ include "lunchables.localfwd" . }}
EOF
chmod +x ~/.local/bin/lunch-portfwd

mkdir -p ~/.local/share/lunchables
kubectl exec deploy/{{ .Release.Name }}-leader-adm -- tar -cz . | tar -xz -C ~/.local/share/lunchables
rm -rf ~/.local/share/lunchables/env
python3 -m venv ~/.local/share/lunchables/env
~/.local/share/lunchables/env/bin/pip install -r ~/.local/share/lunchables/requirements.txt
{{ end -}}

unset -f lunch-adm
