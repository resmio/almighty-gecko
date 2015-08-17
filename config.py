import os

try:
    import local_settings
except ImportError:
    local_settings = object


def get_config(key):
    return (os.environ.get(key) if os.environ.get(key) is not None else
            getattr(local_settings, key, globals().get(key)))


class Config(object):
    DEBUG = False


class ProductionConfig(Config):
    CACHE_TYPE = 'saslmemcached'
    CACHE_MEMCACHED_SERVERS = [os.environ.get('MEMCACHIER_SERVERS')]
    CACHE_MEMCACHED_USERNAME = os.environ.get('MEMCACHIER_USERNAME')
    CACHE_MEMCACHED_PASSWORD = os.environ.get('MEMCACHIER_PASSWORD')


class DevelopmentConfig(Config):
    CACHE_TYPE = 'memcached'
    DEBUG = True
