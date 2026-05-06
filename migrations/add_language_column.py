import asyncpg
import os

async def add_language_column():
    """
    Миграция: добавляет колонку language в таблицу users
    """
    # Получаем URL базы данных из переменных окружения
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    conn = None
    try:
        # Подключаемся к базе данных
        conn = await asyncpg.connect(database_url)
        
        # Проверяем, существует ли колонка language
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'language'
        """
        
        result = await conn.fetch(check_query)
        
        if not result:
            # Добавляем колонку language
            alter_query = """
                ALTER TABLE users 
                ADD COLUMN language VARCHAR(2) DEFAULT 'ru'
            """
            await conn.execute(alter_query)
            print("✅ Column 'language' added successfully to users table")
        else:
            print("ℹ️ Column 'language' already exists in users table")
        
        # Обновляем существующие записи, где language = NULL
        update_query = """
            UPDATE users 
            SET language = 'ru' 
            WHERE language IS NULL
        """
        await conn.execute(update_query)
        print("✅ Updated existing users with default language 'ru'")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
        
    finally:
        if conn:
            await conn.close()


async def drop_language_column():
    """
    Откат миграции: удаляет колонку language (если нужно)
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    conn = None
    try:
        conn = await asyncpg.connect(database_url)
        
        drop_query = """
            ALTER TABLE users 
            DROP COLUMN IF EXISTS language
        """
        await conn.execute(drop_query)
        print("✅ Column 'language' dropped successfully")
        return True
        
    except Exception as e:
        print(f"❌ Rollback error: {e}")
        return False
        
    finally:
        if conn:
            await conn.close()


# Для запуска миграции отдельно
if __name__ == "__main__":
    import asyncio
    asyncio.run(add_language_column())
