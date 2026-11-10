#!/usr/bin/env bash
# Solo en la CONSOLA de la VM que se aislará. Bloquea tráfico entre pares
# por tailscale0, incluyendo SSH, ping, HTTP y Redis, en ambos sentidos.
# No vacía reglas existentes. Tailscale FORWARD no se modifica.
set -euo pipefail
action="${1:-}"
shift || true
if [[ "$action" != "on" && "$action" != "off" ]] || (( $# < 1 )); then
  echo "Uso: sudo bash scripts/particion.sh on|off IP_PEER1 IP_PEER2" >&2; exit 2
fi
for peer in "$@"; do
  [[ "$peer" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2
  for direction in INPUT OUTPUT; do
    if [[ "$direction" == INPUT ]]; then
      rule=(-i tailscale0 -s "$peer/32" -m comment --comment taller1-partition -j DROP)
    else
      rule=(-o tailscale0 -d "$peer/32" -m comment --comment taller1-partition -j DROP)
    fi
    if [[ "$action" == on ]]; then
      if ! iptables -C "$direction" "${rule[@]}" 2>/dev/null; then
        iptables -I "$direction" 1 "${rule[@]}"
      fi
    else
      while iptables -C "$direction" "${rule[@]}" 2>/dev/null; do
        iptables -D "$direction" "${rule[@]}"
      done
    fi
  done
done
echo "$(date -Is) particion=$action peers=$*"
iptables -S INPUT | sed -n '/taller1-partition/p'
iptables -S OUTPUT | sed -n '/taller1-partition/p'
