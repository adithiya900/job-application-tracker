import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from app import app
from extensions import cache

with app.app_context():
    c = cache.cache
    print(type(c))
    print(dir(c))
    
    if hasattr(c, "_client"):
        print("client:", type(c._client))
        print(dir(c._client))
        
        # Test ttl
        c.set("test_key", "val", timeout=300)
        prefix = app.config.get("CACHE_KEY_PREFIX", "")
        ttl = c._client.ttl(f"{prefix}test_key")
        print("TTL test_key:", ttl)
