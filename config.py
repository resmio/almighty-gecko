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
    GA_CLIENT_EMAIL = get_config('GA_CLIENT_EMAIL')
    GA_PRIVATE_KEY = get_config('GA_PRIVATE_KEY')
    GA_SCOPE = get_config('GA_SCOPE')
    GA_ACCOUNT_ID = get_config('GA_ACCOUNT_ID')
    GA_APP_PROPERTY_ID = 'UA-{}-1'.format(GA_ACCOUNT_ID)
    GA_WIDGET_PROPERTY_ID = 'UA-{}-3'.format(GA_ACCOUNT_ID)


class ProductionConfig(Config):
    CACHE_TYPE = 'saslmemcached'
    CACHE_MEMCACHED_SERVERS = [os.environ.get('MEMCACHIER_SERVERS')]
    CACHE_MEMCACHED_USERNAME = os.environ.get('MEMCACHIER_USERNAME')
    CACHE_MEMCACHED_PASSWORD = os.environ.get('MEMCACHIER_PASSWORD')


class DevelopmentConfig(Config):
    CACHE_TYPE = 'null'
    DEBUG = True
