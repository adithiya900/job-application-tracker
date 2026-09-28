def test_postgres_database_is_available(postgres_schema, postgres_engine):
    with postgres_engine.connect() as connection:
        result = connection.exec_driver_sql("SELECT 1")
        assert result.scalar() == 1