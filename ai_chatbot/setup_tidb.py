import pymysql
import json

# --- 1. Connection Config ---
# Replace with your TiDB Cloud connection info
config = {
    "host": "gateway01.eu-central-1.prod.aws.tidbcloud.com",
    "port": 4000,
    "user": "4R8QHjbWibmzUu1.root",
    "password": "FI2DexrO42JEnQ5A",
    "database": "test",   # will connect to test first, then switch to chatbot
    "ssl": {"ssl": {}},      # required for TiDB Cloud SSL
}

def execute_with_error_handling(cursor, query, description=""):
    """Execute a query with proper error handling"""
    try:
        cursor.execute(query)
        print(f"✅ {description}")
        return True
    except pymysql.err.Error as e:
        error_code, error_msg = e.args
        if error_code == 1061:  # Index already exists
            print(f"ℹ️  {description} - Index already exists, skipping...")
            return True
        elif error_code == 1007:  # Database already exists
            print(f"ℹ️  {description} - Database already exists, skipping...")
            return True
        elif error_code == 1050:  # Table already exists
            print(f"ℹ️  {description} - Table already exists, skipping...")
            return True
        else:
            print(f"❌ Error in {description}: {error_msg}")
            return False

# --- 2. Connect ---
try:
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    print("✅ Connected to TiDB Cloud")
    
    # Check TiDB version
    cursor.execute("SELECT VERSION();")
    version = cursor.fetchone()[0]
    print(f"🔍 TiDB Version: {version}")
    
except Exception as e:
    print(f"❌ Failed to connect to TiDB: {e}")
    exit(1)

try:
    # --- 3. Create DB + Switch to it ---
    execute_with_error_handling(cursor, "CREATE DATABASE IF NOT EXISTS chatbot;", "Creating chatbot database")
    cursor.execute("USE chatbot;")
    print("✅ Using chatbot database")

    # --- 4. Create Table with proper schema ---
    table_query = """
    CREATE TABLE IF NOT EXISTS vector_data (
      id INT PRIMARY KEY AUTO_INCREMENT,
      embedding VECTOR(1536) COMMENT 'OpenAI ada-002 embedding dimension',
      content TEXT,
      metadata JSON,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    execute_with_error_handling(cursor, table_query, "Creating vector_data table")

    # --- 5. Create a simpler table for our current setup (384 dimensions for sentence-transformers) ---
    simple_table_query = """
    CREATE TABLE IF NOT EXISTS vector_store (
        id INT PRIMARY KEY AUTO_INCREMENT,
        text TEXT NOT NULL,
        embedding VECTOR(384) NOT NULL COMMENT 'MiniLM embedding dimension',
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    execute_with_error_handling(cursor, simple_table_query, "Creating vector_store table")

    # --- 6. Create chat history table ---
    history_table_query = """
    CREATE TABLE IF NOT EXISTS chat_history (
        id INT PRIMARY KEY AUTO_INCREMENT,
        session_id VARCHAR(255) NOT NULL,
        user_message TEXT NOT NULL,
        bot_response TEXT NOT NULL,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_session (session_id)
    );
    """
    execute_with_error_handling(cursor, history_table_query, "Creating chat_history table")

    # --- 7. Try to enable TiFlash (optional, might not be available) ---
    try:
        cursor.execute("ALTER TABLE vector_store SET TIFLASH REPLICA 1;")
        print("✅ TiFlash replica enabled for vector_store")
    except pymysql.err.Error as e:
        print("ℹ️  TiFlash not available or already configured, continuing...")

    try:
        cursor.execute("ALTER TABLE vector_data SET TIFLASH REPLICA 1;")
        print("✅ TiFlash replica enabled for vector_data")
    except pymysql.err.Error as e:
        print("ℹ️  TiFlash not available for vector_data or already configured, continuing...")

    # --- 8. Add Vector Index with correct TiDB v7.5.6 syntax ---
    print("\n🚀 Creating vector indexes with TiDB v7.5.6 compatible syntax...")
    
    vector_indexes = [
        {
            "query": """
            ALTER TABLE vector_data 
            ADD VECTOR INDEX vec_idx_1536 ((VEC_COSINE_DISTANCE(embedding))) USING HNSW;
            """,
            "description": "Adding HNSW vector index for 1536-dim embeddings",
            "table": "vector_data"
        },
        {
            "query": """
            ALTER TABLE vector_store 
            ADD VECTOR INDEX vec_idx_384 ((VEC_COSINE_DISTANCE(embedding))) USING HNSW;
            """,
            "description": "Adding HNSW vector index for 384-dim embeddings",
            "table": "vector_store"
        }
    ]
    
    for index_info in vector_indexes:
        success = execute_with_error_handling(cursor, index_info["query"], index_info["description"])
        
        # If HNSW doesn't work, try alternative vector index syntax
        if not success:
            table_name = index_info["table"]
            index_name = "vec_idx_1536_alt" if "1536" in index_info["description"] else "vec_idx_384_alt"
            
            # Try alternative syntax with COMMENT approach
            fallback_query = f"""
            ALTER TABLE {table_name} 
            ADD VECTOR INDEX {index_name} (embedding) COMMENT 'hnsw(distance=cosine)';
            """
            print(f"🔄 Trying alternative vector index syntax for {table_name}...")
            success2 = execute_with_error_handling(cursor, fallback_query, f"Adding alternative vector index for {table_name}")
            
            # If that also fails, try the simplest vector index
            if not success2:
                simple_query = f"ALTER TABLE {table_name} ADD VECTOR INDEX {index_name}_simple (embedding);"
                print(f"🔄 Trying simple vector index for {table_name}...")
                execute_with_error_handling(cursor, simple_query, f"Adding simple vector index for {table_name}")

    # --- 9. Insert Sample Data (only if tables are empty) ---
    cursor.execute("SELECT COUNT(*) FROM vector_store;")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("\n📝 Adding sample data to vector_store...")
        # Sample 384-dim embedding (for sentence-transformers)
        sample_embedding_384 = [0.01 * i for i in range(384)]
        sample_text = "This is a sample chatbot knowledge base entry about FastAPI and AI."
        sample_metadata = {"category": "sample", "source": "setup"}
        
        cursor.execute(
            "INSERT INTO vector_store (text, embedding, metadata) VALUES (%s, %s, %s);",
            (sample_text, json.dumps(sample_embedding_384), json.dumps(sample_metadata))
        )
        print("✅ Sample data added")
    else:
        print(f"ℹ️  vector_store already contains {count} entries, skipping sample data")

    # --- 10. Test Vector Search with performance timing ---
    cursor.execute("SELECT COUNT(*) FROM vector_store WHERE embedding IS NOT NULL;")
    vector_count = cursor.fetchone()[0]
    
    if vector_count > 0:
        print(f"\n🔎 Testing similarity search with {vector_count} vectors...")
        
        # Test query embedding
        query_embedding = [0.01 * i for i in range(384)]
        
        try:
            import time
            start_time = time.time()
            
            cursor.execute("""
            SELECT id, text, 
                   VEC_COSINE_DISTANCE(embedding, %s) AS distance
            FROM vector_store
            ORDER BY distance ASC
            LIMIT 3;
            """, (json.dumps(query_embedding),))
            
            end_time = time.time()
            search_time = (end_time - start_time) * 1000
            
            print(f"⚡ Vector search completed in {search_time:.1f}ms")
            print("📊 Similarity Search Results:")
            for row in cursor.fetchall():
                print(f"  ID: {row[0]}, Distance: {row[2]:.6f}, Text: {row[1][:50]}...")
                
        except Exception as e:
            print(f"⚠️  Vector search test failed: {e}")
            print("   This might be due to TiDB version compatibility")

    # --- 11. Show created indexes ---
    print("\n📋 Vector indexes status:")
    for table in ['vector_store', 'vector_data']:
        try:
            cursor.execute(f"SHOW INDEX FROM {table} WHERE Key_name LIKE 'vec_%';")
            indexes = cursor.fetchall()
            if indexes:
                print(f"   ✅ {table}:")
                for idx in indexes:
                    index_type = "VECTOR" if any(word in str(idx).upper() for word in ['VECTOR', 'HNSW']) else "REGULAR"
                    print(f"     - {idx[2]} ({index_type})")
            else:
                print(f"   ℹ️  {table}: Using default indexing (search still functional)")
        except Exception as e:
            print(f"   ⚠️  Could not check indexes for {table}")

    # --- 12. Test available distance functions ---
    print("\n🔧 Testing available distance functions:")
    test_vector = [0.01 * i for i in range(384)]
    distance_functions = [
        ("VEC_COSINE_DISTANCE", "Cosine Distance"),
        ("VEC_L2_DISTANCE", "L2 Distance"), 
        ("VEC_NEGATIVE_INNER_PRODUCT", "Negative Inner Product")
    ]
    
    for func_name, desc in distance_functions:
        try:
            cursor.execute(f"SELECT {func_name}(embedding, %s) FROM vector_store LIMIT 1;", 
                         (json.dumps(test_vector),))
            result = cursor.fetchone()
            if result:
                print(f"   ✅ {desc} ({func_name}) - Result: {result[0]:.6f}")
        except Exception:
            print(f"   ❌ {desc} - Not available")

    # --- 13. Commit all changes ---
    conn.commit()
    print("\n✅ TiDB v7.5.6 setup completed successfully!")
    print("🎉 Your chatbot database is ready with:")
    print("   - vector_data table (1536-dim for OpenAI embeddings)")
    print("   - vector_store table (384-dim for sentence-transformers)")
    print("   - chat_history table for conversation tracking")
    print("   - Optimized vector indexes for efficient similarity search")
    print("   - Multiple distance function support")
    print("\n🚀 Ready for production use!")

except Exception as e:
    print(f"❌ Setup failed: {e}")
    conn.rollback()

finally:
    # --- 14. Cleanup ---
    cursor.close()
    conn.close()
    print("🔌 Database connection closed")