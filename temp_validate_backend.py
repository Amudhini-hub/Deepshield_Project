from backend.config.config import get_config
from backend.services.authentication import get_password_hash

config = get_config()
print('DATABASE_URL=', config.DATABASE_URL)
print('USE_SQLITE_RUNTIME=', getattr(config, 'USE_SQLITE_RUNTIME', None))
print('hash=', get_password_hash('testpassword'))
