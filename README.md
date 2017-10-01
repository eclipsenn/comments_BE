# Comments backend service #

A simple backend service written on aiohttp with postgresql as a storage,
providing a web interface to add, change, remove and restore comments.

A comment can be made for a post or for another comment. 
Each post/comment has a unique ID.

# Application design
It's a python aiohttp web-application, all operations are IO, nothing is
being computed here, so it fits well.

# DB Design
Postgresql database stores the structure of comments.
There're a few ways to represent hierarchical structures in relation DBs,
all of them have its cons and pros.
Some of them serves writes well and reads are complex,
others are better in reads.
So, here's a combination of adjacency list and closure table.
First allows us simple reads for first-level children, helps to sort the
subtree and does not cost us anything(only one FK ref), closure table
helps us to make fast reads for any subtrees. On the other hand, closure
table will cost us excess inserts, in average case it's O(n*log(n)) for 
balanced tree, worst case is O(n^2) when all comments are nested, so tree
becomes a list. Fortunately, it's a very rare case for comments, so
we take it :)
Referential integrity of closure table is handled by trigger functions
at DB level(on-create).
Since one can not remove a comment if it has children, the removing is
designed as setting comment's text to None. This allows simple restoring 
if needed without any overhead.

For simplicity, every entity which user can create(post, page, comment) are
stored in one table, with convenient views to access by type.

installation & running
----------------------

Clone repository locally and set DB host to your docker machine's address.

Application, web-server and DB wrapped into a docker containers,
so simply run

    docker-compose up
    
And find the interface running at <http://host_address:8080>.

API description can be found at index page, simple html forms are
provided for CrUD operations, along with trivial error handling.
Also, a few records are added for simplicity(some posts and comments on them)

To run tests, run

    docker-compose -f tests/docker-compose.test.yml up
    
Tests are run on the same port, so be sure you either use different
hosts for dev/test or stop dev containers before run test ones.