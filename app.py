import streamlit as st
import pandas as pd
import numpy as np
from utils.search_engine import ProductSearchEngine
from utils.database import MongoDBConnection
import warnings
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Si no está instalado dotenv, continuamos sin él

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="Búsqueda de Productos Similares",
    page_icon="🔍",
    layout="wide"
)

# Configuración de MongoDB
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
if not MONGO_CONNECTION_STRING:
    st.error(
        "⚠️ MONGO_CONNECTION_STRING no está configurado. "
        "Por favor, configura esta variable de entorno en un archivo .env"
    )
    st.stop()

MONGO_DATABASE_NAME = os.getenv('MONGO_DATABASE_NAME', 'IPS')

# Función para cargar datos con caché
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data_from_mongodb():
    """Carga los datos de productos y embeddings desde MongoDB"""
    try:
        # Crear conexión
        mongo_conn = MongoDBConnection(MONGO_CONNECTION_STRING, MONGO_DATABASE_NAME)

        # Conectar a MongoDB
        if not mongo_conn.connect():
            st.error("No se pudo establecer conexión con MongoDB")
            return None, None

        with st.spinner("Cargando productos desde MongoDB..."):
            df_products = mongo_conn.get_products()

        with st.spinner("Cargando embeddings desde MongoDB..."):
            df_embeddings = mongo_conn.get_embeddings()

        # Cerrar conexión
        mongo_conn.disconnect()

        if df_products.empty or df_embeddings.empty:
            st.error("No se pudieron cargar los datos desde MongoDB")
            return None, None

        return df_products, df_embeddings

    except Exception as e:
        st.error(f"Error al conectar con MongoDB: {e}")
        return None, None

# Función para formatear el precio
def format_price(price):
    """Formatea el precio con separador de miles"""
    try:
        if pd.isna(price) or price is None:
            return "Precio no disponible"
        return f"${float(price):,.2f}"
    except:
        return "Precio no disponible"

# Función para mostrar tarjeta de producto
def display_product_card(product, show_score=False, card_index=0):
    """Muestra una tarjeta de producto con su información"""
    col1, col2 = st.columns([1, 3])

    with col1:
        if 'image' in product and pd.notna(product['image']):
            try:
                st.image(product['image'], width='stretch')
            except:
                st.image("https://via.placeholder.com/150", width='stretch')
        else:
            st.image("https://via.placeholder.com/150", width='stretch')

    with col2:
        # Validar nombre del producto
        product_name = "Producto sin nombre"
        if 'product_name' in product and pd.notna(product['product_name']) and str(product['product_name']).strip():
            product_name = str(product['product_name'])

        st.subheader(product_name)

        if show_score and 'score' in product and pd.notna(product['score']):
            try:
                score_value = float(product['score'])
                st.metric("Similitud", f"{score_value:.2%}")
            except:
                st.metric("Similitud", "N/A")

        # Validar y mostrar precio
        if 'sale_price' in product:
            st.metric("Precio", format_price(product['sale_price']))

        if 'product_desc' in product and pd.notna(product['product_desc']) and str(product['product_desc']).strip():
            # Limpiar descripción HTML
            desc = str(product['product_desc']).replace('<p>', '').replace('</p>', '')
            # Generar un key único usando el ID del producto y el índice
            unique_key = f"desc_{card_index}"
            if 'product_id' in product:
                unique_key = f"desc_{card_index}_{str(product.get('product_id', ''))[:10]}"

            st.text_area("Descripción",
                        desc[:200] + "..." if len(desc) > 200 else desc,
                        height=100,
                        disabled=True,
                        key=unique_key)

        if 'data_source' in product and pd.notna(product['data_source']):
            st.info(f"Tienda: {product['data_source']}")

        if 'url' in product and pd.notna(product['url']) and str(product['url']).strip():
            st.link_button("🛒 Ver en tienda", product['url'], type="primary")

def main():
    # Título principal
    st.title("Buscador de Productos")
    st.markdown("---")

    # Cargar datos desde MongoDB
    df_products, df_embeddings = load_data_from_mongodb()

    if df_products is None or df_embeddings is None:
        st.stop()

    # Inicializar motor de búsqueda
    @st.cache_resource
    def get_search_engine():
        return ProductSearchEngine()

    search_engine = get_search_engine()

    # Sidebar para configuración
    with st.sidebar:
        st.header("Configuración de Búsqueda")

        num_results = st.slider(
            "Número de resultados por tienda",
            min_value=1,
            max_value=20,
            value=5,
            step=1
        )

        min_score = st.slider(
            "Puntuación mínima de similitud",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05
        )

        only_best_price = st.checkbox(
            "Solo mostrar productos con mejor precio",
            value=False
        )

        st.markdown("---")
        st.header("Estadísticas")
        st.metric("Total de productos", f"{len(df_products):,}")
        st.metric("Total de embeddings", f"{len(df_embeddings):,}")
        st.metric("Tiendas disponibles", df_products['data_source'].nunique() if 'data_source' in df_products.columns else 0)

        st.markdown("---")
        st.info("Conectado a MongoDB")

    # Inicializar session state si no existe
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'search_query_last' not in st.session_state:
        st.session_state.search_query_last = ""

    # Sección principal de búsqueda
    # Modo de búsqueda
    search_mode = st.radio(
        "Modo de búsqueda:",
        ["Buscar por nombre", "Buscar por ID"],
        horizontal=True
    )

    selected_product_id = None

    if search_mode == "Buscar por nombre":
        # Búsqueda por nombre con formulario para capturar Enter
        with st.form(key="search_form"):
            col1, col2 = st.columns([4, 1])

            with col1:
                search_query = st.text_input(
                    "Buscar producto por nombre:",
                    placeholder="Ejemplo: Nevera, Televisor, Microondas..."
                )

            with col2:
                st.write("")  # Espaciado para alinear con el input
                search_submitted = st.form_submit_button("Buscar", type="secondary")

        # Si se presionó el botón de búsqueda (o Enter) y hay texto
        if search_submitted and search_query:
            # Filtrar productos por nombre
            filtered_products = df_products[
                df_products['product_name'].str.contains(
                    search_query, case=False, na=False
                )
            ].head(10)

            # Guardar resultados en session state
            if not filtered_products.empty:
                st.session_state.search_results = filtered_products
                st.session_state.search_query_last = search_query
            else:
                st.session_state.search_results = None
                st.session_state.search_query_last = search_query

        # Mostrar resultados si existen en session state
        if st.session_state.search_results is not None and search_query == st.session_state.search_query_last:
            filtered_products = st.session_state.search_results
            st.write(f"Se encontraron {len(filtered_products)} productos:")

            # Mostrar opciones de productos con botón al lado
            col1, col2 = st.columns([3, 1])

            with col1:
                product_options = filtered_products.apply(
                    lambda x: f"{x['product_name']} - {format_price(x['sale_price'])} ({x['data_source']})",
                    axis=1
                ).tolist()

                selected_index = st.selectbox(
                    "Selecciona un producto:",
                    range(len(product_options)),
                    format_func=lambda x: product_options[x],
                    key="product_selector"
                )

                selected_product_id = filtered_products.iloc[selected_index]['product_id']

            with col2:
                st.write("")  # Espaciado
                search_button = st.button("Buscar Productos Similares",
                                         type="primary",
                                         )
        elif search_query == st.session_state.search_query_last and st.session_state.search_results is None:
            st.warning("No se encontraron productos con ese nombre")
            search_button = False
        else:
            search_button = False

    else:
        # Búsqueda por ID
        col1, col2 = st.columns([4, 1])

        with col1:
            selected_product_id = st.text_input(
                "Ingresa el ID del producto:",
                placeholder="Ejemplo: 68c0b8c2e86ff46e159fc634",
                key="search_id_input"
            )

        with col2:
            st.write("")  # Espaciado
            search_button = st.button("Buscar Productos Similares",
                                     type="primary",
                                     disabled=not selected_product_id)

    # Realizar búsqueda
    if search_button and selected_product_id:
        with st.spinner("Buscando productos similares..."):
            # Verificar que el producto existe
            if selected_product_id not in df_products['product_id'].values:
                st.error("El ID del producto no existe en la base de datos")
            else:
                # Obtener información del producto seleccionado
                selected_product = df_products[
                    df_products['product_id'] == selected_product_id
                ].iloc[0]

                # Mostrar producto seleccionado
                st.markdown("---")
                st.subheader("Producto Seleccionado")
                display_product_card(selected_product, card_index=0)

                # Buscar productos similares
                similar_products = search_engine.get_similar_products_with_details(
                    df_embeddings,
                    df_products,
                    selected_product_id,
                    num_similar_products=num_results,
                    min_score=min_score,
                    only_best_price=only_best_price
                )

                if similar_products is not None and not similar_products.empty:
                    st.markdown("---")
                    st.subheader(f"Se encontraron {len(similar_products)} productos similares")

                    # Agrupar por tienda
                    grouped = similar_products.groupby('data_source')

                    # Crear tabs por tienda
                    tabs = st.tabs([f"{store} ({len(group)})" for store, group in grouped])

                    for tab, (store, products) in zip(tabs, grouped):
                        with tab:
                            for idx, (_, product) in enumerate(products.iterrows()):
                                with st.container():
                                    display_product_card(product, show_score=True, card_index=idx)
                                    if idx < len(products) - 1:
                                        st.markdown("---")
                else:
                    st.warning("No se encontraron productos similares con los criterios especificados")

    # Sección de productos de ejemplo
    with st.expander("Productos de ejemplo para probar"):
        st.write("Aquí hay algunos IDs de productos que puedes usar para probar:")

        example_products = [
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

        cols = st.columns(3)
        for idx, (product_id, name) in enumerate(example_products):
            with cols[idx % 3]:
                st.code(product_id)
                st.caption(name)

if __name__ == "__main__":
    main()