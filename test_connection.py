"""Test PostgreSQL connection"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    url = 'postgresql+asyncpg://nft_user:GiftedForge@localhost:5432/nft_db'
    print(f'Testing connection...')
    print(f'Host: localhost:5432')
    print(f'User: nft_user')
    print(f'Database: nft_db')
    print()
    
    try:
        engine = create_async_engine(url, echo=False)
        async with engine.begin() as conn:
            result = await conn.execute(text('SELECT version()'))
            version = result.scalar()
            print('✓ Connection successful!')
            print(f'PostgreSQL: {version[:60]}...')
        await engine.dispose()
    except Exception as e:
        print(f'✗ Connection failed!')
        print(f'Error: {type(e).__name__}')
        print(f'Message: {e}')
        import traceback
        print('\nFull traceback:')
        traceback.print_exc()

asyncio.run(test())
