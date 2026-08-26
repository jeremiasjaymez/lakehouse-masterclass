#!/usr/bin/env bash
# Ollama + modelos para los Labs 9 y 11.
# Va aparte del setup principal porque son ~5 GB: no todos los alumnos hacen
# los labs de IA, y en Codespaces conviene bajarlos solo si los vas a usar.
set -euo pipefail

echo "==> Instalando Ollama"
curl -fsSL https://ollama.com/install.sh | sh

echo "==> Levantando el servidor en background"
(ollama serve >/tmp/ollama.log 2>&1 &)
sleep 5

echo "==> Descargando modelos (~5 GB, tomate un café)"
ollama pull nomic-embed-text   # embeddings, 768 dimensiones
ollama pull llama3.1           # generación: SQL y respuestas RAG

echo ""
ollama list
echo ""
echo "Listo. Si el server se cae, relevantalo con: ollama serve &"
