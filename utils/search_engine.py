import faiss
import numpy as np
import pandas as pd
import re


class ProductSearchEngine:
    """Motor de búsqueda de productos similares usando FAISS"""

    def __init__(self):
        self.clusters_indexes = []

    def get_cached_index(self, cluster_id, source_cluster):
        """
        Busca un índice FAISS cacheado para un ID de clúster y fuente de datos dados.

        Args:
            cluster_id (int): El ID del clúster.
            source_cluster (str): La fuente de datos del clúster.

        Returns:
            faiss.Index: El índice FAISS cacheado si se encuentra, de lo contrario None.
        """
        for cluster in self.clusters_indexes:
            if cluster['cluster_id'] == cluster_id and cluster['source'] == source_cluster:
                return cluster['index']
        return None

    def get_product_cluster(self, df, product_id):
        """
        Obtiene el clúster al que pertenece un producto dado y el DataFrame de productos dentro de ese clúster.

        Args:
            df (pd.DataFrame): DataFrame con información de productos y clústeres.
            product_id (str): El ID del producto.

        Returns:
            tuple: Una tupla que contiene el DataFrame del clúster del producto, la fila del producto y el ID del clúster.
                   Retorna (None, None, None) si el producto no se encuentra.
        """
        product = df[df['product_id'] == product_id]
        if product.empty:
            return None, None, None

        cluster_id = product['cluster_id'].values[0]
        df_clusters = df[df['cluster_id'] == cluster_id]
        return df_clusters, product, cluster_id

    def get_clusters_group_by_source(self, df):
        """
        Agrupa un DataFrame de clústeres por fuente de datos.

        Args:
            df (pd.DataFrame): DataFrame con información de clústeres.

        Returns:
            pd.core.groupby.generic.DataFrameGroupBy: Un objeto DataFrameGroupBy agrupado por 'data_source'.
        """
        groups = df.groupby('data_source')
        return groups

    def get_cluster_group_by_source(self, df, product_id):
        """
        Obtiene los grupos de clústeres por fuente de datos para el clúster de un producto dado.

        Args:
            df (pd.DataFrame): DataFrame con información de productos y clústeres.
            product_id (str): El ID del producto.

        Returns:
            list: Una lista de diccionarios, cada uno conteniendo el índice FAISS, la fuente de datos y el DataFrame del clúster.
            product: La fila del producto.
                  Retorna None si no se encuentra el clúster del producto.
        """
        product_cluster, product, cluster_id = self.get_product_cluster(df, product_id)

        if product_cluster is None:
            return None, None

        df_by_source = self.get_clusters_group_by_source(product_cluster)
        index_group = []

        for cluster_source in df_by_source.groups:
            source_product_cluster = df_by_source.get_group(cluster_source)

            # Convertir la representación de string del embedding a un array de numpy
            cluster_embeddings = np.array([
                np.fromstring(re.sub(r'[\[\]\n]', '', embedding), sep=' ')
                for embedding in source_product_cluster['normalized_embeddings']
            ])

            index = self.get_cached_index(cluster_id, cluster_source)

            if index is not None:
                index_group.append({
                    'index': index,
                    'source': cluster_source,
                    'data': source_product_cluster
                })
                continue

            index = faiss.IndexFlatIP(cluster_embeddings.shape[1])
            index.add(cluster_embeddings)
            index_group.append({
                'index': index,
                'source': cluster_source,
                'data': source_product_cluster
            })
            self.clusters_indexes.append({
                'source': cluster_source,
                'cluster_id': cluster_id,
                'index': index
            })

        return index_group, product

    def get_similar_products(self, df, product_id, num_similar_products=10, min_score=0.5):
        """
        Busca productos similares a un producto dado utilizando FAISS dentro de su clúster.

        Args:
            df (pd.DataFrame): DataFrame con información de productos y embeddings normalizados.
            product_id (str): El ID del producto.
            num_similar_products (int, optional): El número máximo de productos similares a encontrar. Por defecto es 10.
            min_score (float, optional): La puntuación mínima de similitud para considerar un producto similar. Por defecto es 0.5.

        Returns:
            pd.DataFrame: Un DataFrame con los productos similares encontrados, incluyendo su puntuación de similitud.
                        Retorna None si no se encuentra el clúster del producto.
        """
        # Obtener clusters agrupados por tiendas (data_source)
        cluster_groups, product = self.get_cluster_group_by_source(df, product_id)

        if cluster_groups is None:
            return None

        # Buscar similares
        products_found = []

        for cluster in cluster_groups:
            index = cluster['index']
            df_cluster_data = cluster['data']

            query_vector = np.array([
                np.fromstring(
                    re.sub(r'[\[\]\n]', '', df.loc[df['product_id'] == product_id, 'normalized_embeddings'].values[0]),
                    sep=' '
                )
            ])

            k = num_similar_products + 1
            D, I = index.search(query_vector, k=k)

            # Obtener resultados
            similar_products = df_cluster_data.iloc[I[0]].copy()
            similar_products['score'] = D[0]

            # Convertir score a tipo float para mejorar precisión en filtro
            similar_products['score'] = similar_products['score'].astype(float)

            # Sacar producto que se está buscando de la lista
            similar_products = similar_products[similar_products['product_id'] != product_id]

            # Sacar productos que no tienen score mínimo
            similar_products = similar_products[similar_products['score'] >= min_score]

            # Ordenar productos por puntuación
            similar_products = similar_products.sort_values(by='score', ascending=False)

            # Asegurarse de retornar solo la cantidad requerida por tienda
            similar_products = similar_products.head(num_similar_products)
            products_found.append(similar_products)

        if products_found:
            return pd.DataFrame(pd.concat(products_found))
        else:
            return pd.DataFrame()

    def get_similar_products_with_details(
        self,
        df_embeddings,
        df_products,
        product_id,
        num_similar_products=10,
        min_score=0.5,
        only_best_price=False,
        sort=['score', 'sale_price'],
        ascending=[False, True]
    ):
        """
        Busca productos similares a un producto dado y devuelve sus detalles.

        Args:
            df_embeddings (pd.DataFrame): DataFrame con información de productos y embeddings normalizados.
            df_products (pd.DataFrame): DataFrame con detalles completos de los productos.
            product_id (str): El ID del producto.
            num_similar_products (int, optional): El número máximo de productos similares a encontrar. Por defecto es 10.
            min_score (float, optional): La puntuación mínima de similitud para considerar un producto similar. Por defecto es 0.5.
            only_best_price (bool, optional): Si True, solo retorna productos con mejor precio. Por defecto es False.
            sort (list, optional): Lista de columnas para ordenar los resultados. Por defecto es ['score', 'sale_price'].
            ascending (list, optional): Lista de booleanos para especificar el orden ascendente o descendente. Por defecto es [False, True].

        Returns:
            pd.DataFrame: Un DataFrame con los detalles de los productos similares encontrados, incluyendo su puntuación de similitud.
                        Retorna None si el producto no se encuentra en df_products.
        """
        search_product = df_products[df_products['product_id'] == product_id]

        if search_product.empty:
            return None

        product_name = search_product['product_name'].values[0]
        products_found = self.get_similar_products(df_embeddings, product_id, num_similar_products, min_score)

        if products_found is None or products_found.empty:
            return pd.DataFrame()

        # Columnas de detalles del producto a incluir
        product_details_columns = [
            'product_id', 'product_name', 'product_desc', 'sale_price',
            'category_1_id', 'category_2_id', 'category_3_id',
            'category_1', 'category_2', 'category_3', 'url', 'image', 'data_source'
        ]

        # Filtrar columnas que existen en df_products
        available_columns = [col for col in product_details_columns if col in df_products.columns]

        df_products_details = pd.merge(
            products_found,
            df_products[available_columns],
            on='product_id',
            how='left',
            suffixes=('', '_y')
        )

        # Eliminar columnas duplicadas
        df_products_details = df_products_details.loc[:, ~df_products_details.columns.str.endswith('_y')]

        # Reordenar columnas
        final_columns = ['product_id', 'product_name', 'product_desc', 'sale_price',
                        'data_source', 'cluster_id', 'score']
        final_columns = [col for col in final_columns if col in df_products_details.columns]

        if 'url' in df_products_details.columns:
            final_columns.append('url')
        if 'image' in df_products_details.columns:
            final_columns.append('image')

        df_products_details = df_products_details[final_columns]

        # Solo dejar los productos que tienen mejor precio si se especifica
        if only_best_price:
            product_price = search_product['sale_price'].values[0]
            df_products_details = df_products_details[df_products_details['sale_price'] < product_price]

            if df_products_details.empty:
                return pd.DataFrame()

        # Ordenar resultados
        df_products_details = df_products_details.sort_values(by=sort, ascending=ascending)

        # Filtrar productos con datos válidos
        # Eliminar productos sin nombre o con nombre vacío
        df_products_details = df_products_details[
            df_products_details['product_name'].notna() &
            (df_products_details['product_name'] != '') &
            (df_products_details['product_name'].str.strip() != '')
        ]

        # Eliminar productos sin precio válido
        df_products_details = df_products_details[
            df_products_details['sale_price'].notna() &
            (df_products_details['sale_price'] > 0)
        ]

        return df_products_details