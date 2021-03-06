"""
Test module for db operations.

Currently uses real postgres DB which listens on 5432 port,
so don't use the same docker host for test and dev containers.

Test database is set up with some values, see examples.sql
"""

import pytest
from db import *


@pytest.mark.asyncio
async def test_db_connection(app):
    """Test that engine is correctly initialised and stopped."""
    await init_pg(app, 'test')
    assert not app['db'].closed
    await close_pg(app)
    assert app['db'].closed


@pytest.mark.asyncio
async def test_db_get_comments(conn, init_a_few_db_entries):
    """Test that an existing comment is returned."""
    comments = await db_get_comments(conn, 'user1')
    assert all((comment.creator == 'user1' for comment in comments))


@pytest.mark.asyncio
async def test_db_get_comments_not_found(conn, init_a_few_db_entries):
    """Test that Exception is raised when no comments found."""
    with pytest.raises(RecordNotFound):
        await db_get_comments(conn, 'user3')


@pytest.mark.asyncio
async def test_db_create_comment(conn, init_a_few_db_entries):
    """Test that a comment is added for an existing user-entity pair."""
    await db_create_comment(conn, 'user2', 'Yana made test', 'comment', 1)
    comments = await db_get_comments(conn, 'user2')
    assert any(map(lambda x: 'Yana made test' in x.text, comments))


@pytest.mark.asyncio
async def test_db_create_comment_parent_not_found(conn, init_a_few_db_entries):
    """
    Test that creation fails if wrong parent entity is provided.

    This is 7th row, so entity_id = 8 shouldn't exist.
    """
    with pytest.raises(ExecuteException):
        await db_create_comment(conn, 'user2', 'Fake parent entity', 'post', 3)


@pytest.mark.asyncio
async def test_db_get_1lvl_comments(conn, init_a_few_db_entries):
    """ Test that all first-level comments get returned."""
    await db_create_comment(conn, 'user1', 'Dima made lvl1 comment', 'comment', 2)
    comments = await db_get_1lvl_comments(conn, 'comment', 2)
    assert any(map(lambda x: 'Dima made lvl1 comment' in x.text, comments))


@pytest.mark.asyncio
async def test_db_get_lvl1_comments_not_found(conn, init_a_few_db_entries):
    """
    Test that RecordNotFound is raised

    when no lvl comments found.
    """
    with pytest.raises(RecordNotFound):
        await db_get_1lvl_comments(conn, 'comment', 3)


@pytest.mark.asyncio
async def test_db_change_comment(conn, init_a_few_db_entries):
    """Test that comment gets changed properly."""
    await db_change_comment(conn, 'user1', 3, 'Dima changed comment')
    comments = await db_get_comments(conn, 'user1')
    changed_comment = [c.text for c in comments if c.id == 3]
    assert changed_comment == ['Dima changed comment']


@pytest.mark.asyncio
async def test_db_change_comment_not_found(conn, init_a_few_db_entries):
    """Test that ExecutionException is raised if no cooment found."""
    with pytest.raises(ExecuteException):
        await db_change_comment(conn, 'user1', 7, 'Dima changed comment')


@pytest.mark.asyncio
async def test_db_delete_comment(conn, init_a_few_db_entries):
    """
    Test that comment gets removed properly.

    Basically, removing just sets text to None.
    """
    await db_delete_comment(conn, 'user1', 3)
    comments = await db_get_comments(conn, 'user1')
    assert [c.text for c in comments if c.id == 3] == [None]


@pytest.mark.asyncio
async def test_db_delete_comment(conn, init_a_few_db_entries):
    """Test that comment gets removed properly."""
    await db_delete_comment(conn, 'user1', 3)
    comments = await db_get_comments(conn, 'user1')
    assert [c.text for c in comments if c.id == 3] == []


@pytest.mark.asyncio
async def test_db_delete_comment_has_children(conn, init_a_few_db_entries):
    """ Test that ExecutionException is raised if comment has children."""
    with pytest.raises(ExecuteException):
        await db_delete_comment(conn, 'user1', 1)


@pytest.mark.asyncio
async def test_db_get_child_comments(conn, init_a_few_db_entries):
    """ Test that all child comments get returned."""
    comments = await db_get_child_comments(conn, 1)
    comment_texts = [c.text for c in comments]
    assert (
        len(comment_texts) == 1 and
        'dima commented some comment' in comment_texts
    )


@pytest.mark.asyncio
async def test_db_get_child_comments_not_found(conn, init_a_few_db_entries):
    """
    Test that RecordNotFound is raised

    when no lvl comments found.
    """
    with pytest.raises(RecordNotFound):
        await db_get_child_comments(conn, 5)


@pytest.mark.asyncio
async def test_db_get_full_tree(conn, init_a_few_db_entries):
    """Test that the full tree of comments gets returned."""
    comments = await db_get_full_tree(conn, 'post', 1)
    comment_texts = [c.text for c in comments]
    assert (
        len(comment_texts) == 3 and
        'some post' in comment_texts and
        'new comment by dima' in comment_texts and
        'dima commented some comment' in comment_texts
    )


@pytest.mark.asyncio
async def test_db_get_full_tree_not_found(conn, init_a_few_db_entries):
    """"""
    with pytest.raises(RecordNotFound):
        await db_get_full_tree(conn, 'comment', 5)


@pytest.mark.asyncio
async def test_db_get_history(conn, init_a_few_db_entries):
    """Test that history gets returned correctly."""
    results = await db_get_history(conn, 'user1', None, None, 3)
    assert [(r.text, r.action) for r in results] == [('dima commented some comment', 'create')]


@pytest.mark.asyncio
async def test_db_get_history_not_found(conn, init_a_few_db_entries):
    """
    Test that RecordNotFound is raised

    when no history were found.
    """
    with pytest.raises(RecordNotFound):
        await db_get_history(conn, 'user1', None, None, 2)


@pytest.mark.asyncio
async def test_db_get_search_history(conn, init_a_few_db_entries):
    """
    Test that when a history is fetched

    the search_history table gets populated with the record.
    """
    await db_get_history(conn, 'user1', None, None, 3)
    results = await db_get_search_history(conn, 'user1')
    assert [(r.user, r.root_entity_id) for r in results] == [('user1', 3)]


@pytest.mark.asyncio
async def test_db_get_search_history_not_found(conn, init_a_few_db_entries):
    """
    Test that RecordNotFound is raised

    when no history searches were found.
    """
    with pytest.raises(RecordNotFound):
        await db_get_search_history(conn, 'user1')
