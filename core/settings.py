config = {
    'dev': {
        'postgres': {
            'database': 'comments_db',
            'user': 'dmishin',
            'password': 'dmishin',
            'host': '192.168.99.100',
            'port': 5432,
            'minsize': 1,
            'maxsize': 5,
        },
        'host': '127.0.0.1',
        'port': 8080,
    },
    'test': {
        'postgres': {
            'database': 'test_comments_db',
            'user': 'dmishin',
            'password': 'dmishin',
            'host': '192.168.99.100',
            'port': 5433,
            'minsize': 1,
            'maxsize': 5,
        },
        'host': '127.0.0.1',
        'port': 8080,
    }
}
