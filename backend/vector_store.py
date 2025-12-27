from pymilvus import MilvusClient, DataType

def initialize_milvus(db_path="./milvus_database.db"):
    """
    Initializes the Milvus database with the Hyper-Node schema.
    """
    client = MilvusClient(db_path)

    collection_name = "chakravyuh_knowledge_graph"

    # Check if collection exists
    if client.has_collection(collection_name):
        # For this setup, we might want to preserve data or drop.
        # Given "Architecture" focus, let's keep it if it exists, or create if not.
        # But if the schema is different (from old app), we might need to drop.
        # The old app used "my_collection" or "LangChainCollection".
        # This is a new collection "chakravyuh_knowledge_graph".
        pass
    else:
        # Define Schema
        schema = MilvusClient.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
            description="Chakravyuh Hyper-Node Schema"
        )

        # 1. UUID (Primary Key)
        schema.add_field(field_name="uuid", datatype=DataType.VARCHAR, max_length=100, is_primary=True)

        # 2. Modality (Enum-like string)
        schema.add_field(field_name="modality", datatype=DataType.VARCHAR, max_length=20)

        # 3. Content (Raw text or Caption)
        schema.add_field(field_name="content_blob", datatype=DataType.VARCHAR, max_length=65535)

        # 4. Dense Embedding (Text/Caption - 384 dim for MiniLM)
        schema.add_field(field_name="embedding_dense", datatype=DataType.FLOAT_VECTOR, dim=384)

        # 5. CLIP Embedding (Visual - 512 dim - Optional/Placeholder for now)
        # Using 384 for now to simplify "Shared Space" simulation with text models if CLIP fails,
        # but report says 512. I'll use 512 to be spec-compliant, and pad if needed.
        schema.add_field(field_name="embedding_clip", datatype=DataType.FLOAT_VECTOR, dim=512)

        # 6. Metadata (stored as JSON/Dynamic) is handled by enable_dynamic_field=True

        # 7. Parent ID (for context)
        schema.add_field(field_name="parent_id", datatype=DataType.VARCHAR, max_length=100)

        # Indexing parameters
        index_params = client.prepare_index_params()

        index_params.add_index(
            field_name="embedding_dense",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128}
        )

        index_params.add_index(
            field_name="embedding_clip",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128}
        )

        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )
        print(f"Collection {collection_name} created successfully.")

    return client, collection_name
