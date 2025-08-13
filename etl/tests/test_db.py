from src.db import get_engine
with get_engine().connect() as c:
    print("ping:", c.exec_driver_sql("select 1").scalar() == 1)