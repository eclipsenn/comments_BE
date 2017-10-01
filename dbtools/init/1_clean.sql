DROP TYPE IF EXISTS ancestor_type CASCADE;
DROP TYPE IF EXISTS action_type CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP VIEW IF EXISTS comments;
DROP VIEW IF EXISTS posts;
DROP VIEW IF EXISTS pages;
DROP TABLE IF EXISTS history CASCADE;
DROP TRIGGER IF EXISTS tr_create_comment ON entities CASCADE;
DROP TRIGGER IF EXISTS tr_update_comment ON entities CASCADE;
DROP TABLE IF EXISTS search_history CASCADE;
DROP TABLE IF EXISTS entities_closure_table CASCADE;
