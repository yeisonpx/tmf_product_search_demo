import pandas as pd
from pymongo import MongoClient
import streamlit as st


class MongoDBConnection:
    """Maneja la conexión y consultas a MongoDB"""

    def __init__(self, connection_string, database_name="IPS"):
        """
        Inicializa la conexión a MongoDB.

        Args:
            connection_string (str): String de conexión a MongoDB
            database_name (str): Nombre de la base de datos a usar
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None

    def connect(self):
        """Establece la conexión a MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            # Verificar conexión
            self.client.server_info()
            return True
        except Exception as e:
            st.error(f"Error al conectar a MongoDB: {e}")
            return False

    def disconnect(self):
        """Cierra la conexión a MongoDB"""
        if self.client:
            self.client.close()

    def get_products(self, limit=None):
        """
        Obtiene los productos de la colección stores_products_final.

        Args:
            limit (int, optional): Número máximo de documentos a retornar

        Returns:
            pd.DataFrame: DataFrame con los productos
        """
        try:
            collection = self.db['stores_products_final']

            # Crear query
            if limit:
                cursor = collection.find().limit(limit)
            else:
                cursor = collection.find()

            # Convertir a lista de diccionarios
            products = list(cursor)

            if not products:
                st.warning("No se encontraron productos en la base de datos")
                return pd.DataFrame()

            # Convertir a DataFrame
            df_products = pd.DataFrame(products)

            # Eliminar el campo _id de MongoDB si existe
            if '_id' in df_products.columns:
                df_products = df_products.drop('_id', axis=1)

            return df_products

        except Exception as e:
            st.error(f"Error al obtener productos: {e}")
            return pd.DataFrame()

    def get_embeddings(self, limit=None):
        """
        Obtiene los embeddings de la colección stores_products_embeddings.

        Args:
            limit (int, optional): Número máximo de documentos a retornar

        Returns:
            pd.DataFrame: DataFrame con los embeddings
        """
        try:
            collection = self.db['stores_products_embeddings']

            # Crear query
            if limit:
                cursor = collection.find().limit(limit)
            else:
                cursor = collection.find()

            # Convertir a lista de diccionarios
            embeddings = list(cursor)

            if not embeddings:
                st.warning("No se encontraron embeddings en la base de datos")
                return pd.DataFrame()

            # Convertir a DataFrame
            df_embeddings = pd.DataFrame(embeddings)

            # Eliminar el campo _id de MongoDB si existe
            if '_id' in df_embeddings.columns:
                df_embeddings = df_embeddings.drop('_id', axis=1)

            return df_embeddings

        except Exception as e:
            st.error(f"Error al obtener embeddings: {e}")
            return pd.DataFrame()

    def get_product_by_id(self, product_id):
        """
        Obtiene un producto específico por su ID.

        Args:
            product_id (str): ID del producto

        Returns:
            dict: Documento del producto o None si no se encuentra
        """
        try:
            collection = self.db['stores_products_final']
            product = collection.find_one({'product_id': product_id})

            if product and '_id' in product:
                del product['_id']

            return product

        except Exception as e:
            st.error(f"Error al obtener producto: {e}")
            return None

    def search_products_by_name(self, search_query, limit=20):
        """
        Busca productos por nombre.

        Args:
            search_query (str): Término de búsqueda
            limit (int): Número máximo de resultados

        Returns:
            pd.DataFrame: DataFrame con los productos encontrados
        """
        try:
            collection = self.db['stores_products_final']

            # Búsqueda con expresión regular (case-insensitive)
            query = {
                'product_name': {
                    '$regex': search_query,
                    '$options': 'i'
                }
            }

            cursor = collection.find(query).limit(limit)
            products = list(cursor)

            if not products:
                return pd.DataFrame()

            df_products = pd.DataFrame(products)

            if '_id' in df_products.columns:
                df_products = df_products.drop('_id', axis=1)

            return df_products

        except Exception as e:
            st.error(f"Error al buscar productos: {e}")
            return pd.DataFrame()

    def get_embedding_by_product_id(self, product_id):
        """
        Obtiene el embedding de un producto específico.

        Args:
            product_id (str): ID del producto

        Returns:
            dict: Documento del embedding o None si no se encuentra
        """
        try:
            collection = self.db['stores_products_embeddings']
            embedding = collection.find_one({'product_id': product_id})

            if embedding and '_id' in embedding:
                del embedding['_id']

            return embedding

        except Exception as e:
            st.error(f"Error al obtener embedding: {e}")
            return None

    def get_products_by_cluster(self, cluster_id):
        """
        Obtiene todos los productos de un clúster específico.

        Args:
            cluster_id (int): ID del clúster

        Returns:
            pd.DataFrame: DataFrame con los productos del clúster
        """
        try:
            # Primero obtener los product_ids del clúster desde embeddings
            embeddings_collection = self.db['stores_products_embeddings']
            embeddings_cursor = embeddings_collection.find({'cluster_id': cluster_id})
            embeddings = list(embeddings_cursor)

            if not embeddings:
                return pd.DataFrame()

            df_embeddings = pd.DataFrame(embeddings)

            # Obtener los detalles de productos
            products_collection = self.db['stores_products_final']
            product_ids = df_embeddings['product_id'].tolist()

            products_cursor = products_collection.find({
                'product_id': {'$in': product_ids}
            })
            products = list(products_cursor)

            if not products:
                return pd.DataFrame()

            df_products = pd.DataFrame(products)

            # Eliminar _id si existe
            for df in [df_embeddings, df_products]:
                if '_id' in df.columns:
                    df.drop('_id', axis=1, inplace=True)

            # Merge embeddings con productos
            df_result = pd.merge(df_embeddings, df_products, on='product_id', how='left')

            return df_result

        except Exception as e:
            st.error(f"Error al obtener productos del clúster: {e}")
            return pd.DataFrame()