from alembic import op


def upgrade_user_memories_vec(dim: int = 1024) -> None:
    """Create the sqlite-vec virtual table + triggers that mirror embeddings
    from `user_memories` into `user_memories_vec`. Called from an Alembic
    migration after the main `user_memories` table is created."""
    op.execute(
        f"CREATE VIRTUAL TABLE user_memories_vec USING vec0("
        f"rowid INTEGER PRIMARY KEY, text_embedding float[{dim}])"
    )
    op.execute(
        """
        CREATE TRIGGER user_memories_embed_text
        AFTER INSERT ON user_memories
        BEGIN
            INSERT INTO user_memories_vec(rowid, text_embedding)
            VALUES (new.rowid, new.text_embedding);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER user_memories_embed_update
        AFTER UPDATE OF text_embedding ON user_memories
        BEGIN
            UPDATE user_memories_vec
            SET text_embedding = NEW.text_embedding
            WHERE rowid = NEW.rowid;
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER user_memories_embed_delete
        AFTER DELETE ON user_memories
        BEGIN
            DELETE FROM user_memories_vec WHERE rowid = OLD.rowid;
        END
        """
    )


def downgrade_user_memories_vec() -> None:
    op.execute("DROP TRIGGER IF EXISTS user_memories_embed_delete")
    op.execute("DROP TRIGGER IF EXISTS user_memories_embed_update")
    op.execute("DROP TRIGGER IF EXISTS user_memories_embed_text")
    op.execute("DROP TABLE IF EXISTS user_memories_vec")
