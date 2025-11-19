"""
Cassandra Database Connection
"""

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CassandraDB:
    def __init__(self, hosts=['cassandra'], port=9042):
        self.hosts = hosts
        self.port = port
        self.session = None
        self.cluster = None
    
    def connect(self):
        """Connect to Cassandra"""
        try:
            self.cluster = Cluster(self.hosts, port=self.port)
            self.session = self.cluster.connect('hsbc')
            logger.info("✅ Connected to Cassandra")
            return self.session
        except Exception as e:
            logger.error(f"❌ Cassandra connection failed: {str(e)}")
            raise
    
    def close(self):
        """Close connection"""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Cassandra connection closed")

# Global instance
db = CassandraDB()
