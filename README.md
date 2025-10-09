# Búsqueda de Productos Similares con FAISS

Aplicación de Streamlit para buscar productos similares utilizando FAISS (Facebook AI Similarity Search) y embeddings pre-calculados, con datos almacenados en MongoDB.

## Descripción

Esta aplicación permite buscar productos similares basándose en embeddings vectoriales pre-calculados. Utiliza FAISS para realizar búsquedas eficientes de similitud por coseno dentro de clústeres de productos. Los datos se obtienen directamente desde una base de datos MongoDB.

## Características

- Conexión directa a MongoDB para obtener datos
- Búsqueda de productos por nombre o ID
- Búsqueda de similitud usando FAISS
- Filtrado por puntuación mínima de similitud
- Opción para mostrar solo productos con mejor precio
- Agrupación de resultados por tienda
- Visualización de imágenes y descripciones de productos
- Caché inteligente para mejorar el rendimiento

## Requisitos Previos

- Python 3.8+
- Conexión a Internet (para acceder a MongoDB Atlas)
- Credenciales de MongoDB (incluidas en el código)

## Instalación

1. Clonar o descargar el proyecto

2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Ejecutar la aplicación:
```bash
streamlit run app.py
```

2. La aplicación se abrirá en tu navegador en `http://localhost:8501`

3. Seleccionar el modo de búsqueda:
   - **Por nombre**: Buscar productos escribiendo parte del nombre
   - **Por ID**: Ingresar directamente el ID del producto

4. Configurar los parámetros de búsqueda en la barra lateral:
   - Número de resultados por tienda
   - Puntuación mínima de similitud
   - Opción de mostrar solo productos con mejor precio

5. Hacer clic en "Buscar Productos Similares"

## Estructura del Proyecto

```
tmf_product_search_demo/
│
├── app.py                      # Aplicación principal de Streamlit
├── config.py                   # Configuración de la aplicación
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Este archivo
│
└── utils/
    ├── search_engine.py        # Motor de búsqueda con FAISS
    └── database.py             # Conexión y consultas a MongoDB
```

## Base de Datos MongoDB

La aplicación se conecta a MongoDB Atlas con las siguientes colecciones:

- **stores_products_final**: Contiene el catálogo completo de productos con sus detalles
- **stores_products_embeddings**: Contiene los embeddings normalizados y clústeres de cada producto

### Configuración de MongoDB

La conexión a MongoDB se puede configurar mediante variables de entorno:

```bash
export MONGO_CONNECTION_STRING="tu_connection_string"
export MONGO_DATABASE_NAME="IPS"
```

Si no se especifican, la aplicación usa los valores por defecto configurados en `config.py`.

## Algoritmo de Búsqueda

1. **Clustering**: Los productos están pre-agrupados en clústeres
2. **Indexación FAISS**: Se crea un índice FAISS por cada clúster y tienda
3. **Búsqueda de Similitud**: Se utiliza búsqueda por producto interno (Inner Product)
4. **Filtrado**: Se aplican filtros de puntuación mínima y precio
5. **Ordenamiento**: Los resultados se ordenan por puntuación de similitud

## Productos de Ejemplo

La aplicación incluye una lista de productos de ejemplo que puedes usar para probar:

- Nevera: `68c0b8c2e86ff46e159fc634`
- Estufa: `68cb71c57c7a0903962890c3`
- TV: `68c0b8d9e86ff46e159fc784`
- Microondas: `68cb71c47c7a090396288ff3`
- Air Fryer: `68be229a8821a2812cbad1ce`

## Notas Técnicas

- Los embeddings deben estar normalizados para que la búsqueda por producto interno funcione correctamente
- La aplicación utiliza caché de Streamlit para mejorar el rendimiento (TTL de 1 hora para datos de MongoDB)
- Los índices FAISS se cachean en memoria para búsquedas más rápidas
- La conexión a MongoDB se realiza de forma segura mediante MongoDB Atlas
- Los datos se cargan una vez y se mantienen en caché para optimizar el rendimiento

## Solución de Problemas

1. **Error de conexión a MongoDB**: Verificar que tienes conexión a Internet y que las credenciales son correctas
2. **Datos vacíos**: Verificar que las colecciones en MongoDB contienen datos
3. **Rendimiento lento**: La primera carga puede ser lenta debido a la descarga de datos desde MongoDB. Las siguientes búsquedas serán más rápidas gracias al caché

## Dependencias Principales

- **streamlit**: Framework para la interfaz web
- **pandas**: Manejo de datos tabulares
- **numpy**: Operaciones con arrays para embeddings
- **faiss-cpu**: Búsqueda de similitud vectorial
- **pymongo**: Cliente de MongoDB para Python
- **dnspython**: Requerido para conexiones MongoDB+SRV