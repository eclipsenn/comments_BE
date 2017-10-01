"""
Test module for views, checks the right data passed to the user.

TODO: DB calls should be mocked here.
"""

import pytest


@pytest.mark.asyncio
async def test_index(test_client, comments_app):
    """Test the start page which contains API description."""
    client = await test_client(comments_app)
    resp = await client.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert 'API:' in text
