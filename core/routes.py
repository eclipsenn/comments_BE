from views import *


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/{user}/create_comment', create_comment_form)
    app.router.add_post('/{user}/create_comment', create_comment)
    app.router.add_get('/{user}/get_comments', get_comments)
    app.router.add_get('/{user}/lvl1', get_1lvl_comments, name='lvl1')
    app.router.add_get('/{user}/change_comment', change_comment_form)
    app.router.add_post('/{user}/change_comment', change_comment)
    app.router.add_get('/{user}/delete_comment', delete_comment_form)
    app.router.add_post('/{user}/delete_comment', delete_comment)
    app.router.add_get('/{user}/get_children', get_child_comments)
    app.router.add_get('/{user}/get_full_tree', get_full_tree)
    app.router.add_get('/{user}/get_history', get_history_form)
    app.router.add_post('/{user}/get_history', get_history)
    app.router.add_get('/{user}/search_history', get_search_history)
    app.router.add_post('/{user}/search_history', get_history)
