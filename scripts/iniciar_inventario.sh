#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ "$#" == 1 && "$1" =~ ^[1-3]$ ]] || { echo "Uso: bash scripts/iniciar_inventario.sh ID"; exit 2; }
[[ -f .env ]] || { echo "Ejecutar primero preparar_inventario.sh"; exit 1; }
source .env
mkdir -p logs
python3 -u coordinador/nodo.py "$1" --inventario 2>&1 | tee -a "logs/nodo1_inventario.log"
