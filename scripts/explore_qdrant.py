"""
Script de exploración de Qdrant — Fase 2
Objetivo: entender los conceptos básicos de insert + search antes de la Fase 5.

Conceptos clave:
- Collection: tabla de vectores (como una tabla en SQL)
- Vector: lista de números que representa el "significado" de un texto
- Payload: metadata que va junto al vector (el texto original, ID, etc.)
- Search: buscar los N vectores más similares a un vector de consulta
"""

import json
import urllib.request
import urllib.error

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "test_memoria"

# Usamos vectores cortos (4 dimensiones) solo para demostrar el concepto.
# En producción usaremos all-MiniLM-L6-v2 que genera vectores de 384 dimensiones.
VECTOR_SIZE = 4


def request(method: str, path: str, body: dict | None = None) -> dict:
    """Helper para hacer requests HTTP sin dependencias externas."""
    url = f"{QDRANT_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def main():
    print("=== Exploración de Qdrant ===\n")

    # 1. Crear una collection (si ya existe, la borramos primero)
    print("1. Creando collection 'test_memoria'...")
    request("DELETE", f"/collections/{COLLECTION_NAME}")
    result = request("PUT", f"/collections/{COLLECTION_NAME}", {
        "vectors": {
            "size": VECTOR_SIZE,
            "distance": "Cosine"  # Mide similitud semántica (0=opuesto, 1=idéntico)
        }
    })
    print(f"   → {result}\n")

    # 2. Insertar algunos "recuerdos" con sus vectores y metadata
    # En producción, los vectores los genera el modelo de embeddings.
    # Acá los ponemos a mano para entender la estructura.
    print("2. Insertando puntos (vectores + metadata)...")
    points = [
        {
            "id": 1,
            "vector": [0.9, 0.1, 0.1, 0.0],  # "orientado a trabajo"
            "payload": {
                "texto": "Apliqué a una oferta de AI Engineer en Mercado Libre",
                "categoria": "trabajo",
                "fecha": "2026-05-24"
            }
        },
        {
            "id": 2,
            "vector": [0.8, 0.2, 0.0, 0.1],  # "similar a trabajo"
            "payload": {
                "texto": "Tengo entrevista técnica el viernes para ML Engineer",
                "categoria": "trabajo",
                "fecha": "2026-05-24"
            }
        },
        {
            "id": 3,
            "vector": [0.1, 0.9, 0.1, 0.0],  # "orientado a aprendizaje"
            "payload": {
                "texto": "Terminé el módulo de Docker del curso de DevOps",
                "categoria": "aprendizaje",
                "fecha": "2026-05-24"
            }
        },
        {
            "id": 4,
            "vector": [0.0, 0.1, 0.9, 0.0],  # "orientado a personal"
            "payload": {
                "texto": "Reunión familiar el domingo en casa de la abuela",
                "categoria": "personal",
                "fecha": "2026-05-24"
            }
        },
    ]
    result = request("PUT", f"/collections/{COLLECTION_NAME}/points", {"points": points})
    print(f"   → {result}\n")

    # 3. Buscar por similitud semántica
    # Preguntamos: "¿qué recuerdos son similares a algo relacionado con trabajo?"
    print("3. Buscando recuerdos similares a [0.85, 0.15, 0.0, 0.0] (similar a 'trabajo')...")
    result = request("POST", f"/collections/{COLLECTION_NAME}/points/search", {
        "vector": [0.85, 0.15, 0.0, 0.0],
        "limit": 3,
        "with_payload": True
    })
    print("   Resultados (ordenados por relevancia):")
    for hit in result.get("result", []):
        score = hit["score"]
        texto = hit["payload"]["texto"]
        print(f"   [{score:.3f}] {texto}")
    print()

    # 4. Verificar que los datos persisten
    print("4. Verificando colecciones existentes en Qdrant...")
    result = request("GET", "/collections")
    for col in result.get("result", {}).get("collections", []):
        print(f"   → Collection: {col['name']}")

    print("\n✅ Exploración completa.")
    print("   → Los vectores más cercanos al query aparecen primero.")
    print("   → En Fase 5, los vectores los genera all-MiniLM-L6-v2 automáticamente.")
    print("   → Los payloads pueden contener cualquier metadata JSON.")


if __name__ == "__main__":
    main()
