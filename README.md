# Comments backend service #

A simple backend service written on aiohttp with postgresql as a storage,
providing a web interface to add, change, remove and restore comments.

A comment can be made for a post or for another comment. 
Each post/comment has a unique ID.

TODO: add the interface description

installation & running
----------------------

This is wrapped into a docker containers, so simply run

    docker-compose up
    
And find the interface running at <http://host_address:8080>.

TODO: make host address dynamically calculated for DB connection.
Until this is done, need to specify the DB host address in settings.py.