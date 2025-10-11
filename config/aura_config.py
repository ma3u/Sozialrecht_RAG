"""
Neo4j Aura Cloud Configuration
Manages credentials for Aura deployment
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class AuraConfig:
    """Neo4j Aura Cloud Configuration"""

    def __init__(self):
        """Load Aura credentials from environment"""
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')

        # Detect if Aura
        self.is_aura = '+s' in self.uri or 'neo4j.io' in self.uri

    def get_credentials(self):
        """Get connection credentials"""
        return {
            'uri': self.uri,
            'username': self.username,
            'password': self.password,
            'is_aura': self.is_aura
        }

    def validate(self):
        """Validate Aura configuration"""
        if not self.uri or not self.username or not self.password:
            raise ValueError("Missing Neo4j credentials! Check .env file")

        if self.is_aura:
            if not self.uri.startswith('neo4j+s://'):
                raise ValueError(f"Aura URI must start with neo4j+s:// (got: {self.uri})")
            if '.databases.neo4j.io' not in self.uri:
                raise ValueError(f"Aura URI must contain .databases.neo4j.io (got: {self.uri})")

        return True

    def __str__(self):
        """String representation (hides password)"""
        return f"""
Neo4j Configuration:
  URI: {self.uri}
  Username: {self.username}
  Password: {'*' * len(self.password) if self.password else 'NOT SET'}
  Type: {'Aura Cloud' if self.is_aura else 'Local'}
"""


if __name__ == "__main__":
    config = AuraConfig()
    print(config)

    try:
        config.validate()
        print("✅ Configuration valid!")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n📝 Setup instructions:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your Aura credentials")
        print("3. URI format: neo4j+s://xxxxx.databases.neo4j.io")
