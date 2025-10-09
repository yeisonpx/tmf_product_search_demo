"""
Configuración de la aplicación
"""

import os

# Configuración de MongoDB
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
if not MONGO_CONNECTION_STRING:
    raise ValueError(
        "MONGO_CONNECTION_STRING no está configurado. "
        "Por favor, configura esta variable de entorno."
    )

MONGO_DATABASE_NAME = os.getenv('MONGO_DATABASE_NAME', 'IPS')

# Colecciones de MongoDB
PRODUCTS_COLLECTION = 'stores_products_final'
EMBEDDINGS_COLLECTION = 'stores_products_embeddings'

# Configuración de caché
CACHE_TTL = 3600  # 1 hora en segundos

# Productos de ejemplo para pruebas
EXAMPLE_PRODUCTS = [
    ('68c0b8c2e86ff46e159fc634', 'Nevera'),
    ('68cb71c57c7a0903962890c3', 'Estufa'),
    ('68c0b8d9e86ff46e159fc784', 'TV'),
    ('68be229a8821a2812cbacd0f', 'Pechuga de Pavo'),
    ('68be229a8821a2812cbacb5e', 'Pechuga de Pollo'),
    ('68cb71c47c7a090396288ff3', 'Microondas'),
    ('68cb71c97c7a09039628956a', 'Abanico'),
    ('68c0b872e86ff46e159fc1ea', 'Aceite capilar'),
    ('68be229a8821a2812cbaff0f', 'Cable USB'),
    ('68be229a8821a2812cbad1ce', 'Air Fryer'),
    ('68cb71c87c7a090396289421', 'Café'),
    ('68cb71d77c7a09039628a179', 'Yogurt Griego'),
]