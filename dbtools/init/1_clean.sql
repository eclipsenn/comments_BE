DROP TYPE IF EXISTS entity_type CASCADE;
DROP TYPE IF EXISTS action_type CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS history CASCADE;
DROP TRIGGER IF EXISTS tr_create_comment_to_history ON entities CASCADE;
DROP TRIGGER IF EXISTS tr_update_comment_to_history ON entities CASCADE;
DROP TRIGGER IF EXISTS tr_delete_comment_to_history ON entities CASCADE;
DROP TABLE IF EXISTS search_history CASCADE;
DROP TABLE IF EXISTS entities_closure_table CASCADE;
DROP TRIGGER IF EXISTS create_comment_to_closure ON entities CASCADE;
DROP TRIGGER IF EXISTS delete_comment_to_closure ON entities CASCADE;
