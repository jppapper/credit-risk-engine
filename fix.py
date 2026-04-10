eod_marks = '''import os
from datetime import date
from sqlalchemy.orm import Session
from src.database.models import EODMark, engine

def save_eod_mark(result: dict, mark_date: date = None):
    if mark_date is None:
        mark_date = date.today()
    with Session(engine) as session:
        mark = EODMark(
            instrument_id=result["instrument_id"],
            mark_date=mark_date,
            product=result["product"],
            spread_bps=result.get("spread_bps"),
            rate=result.get("rate"),
            dirty_price=result.get("dirty_price"),
            upfront=result.get("upfront"),
            cs01=result.get("cs01"),
            dv01=result.get("dv01"),
            notional=result.get("notional")
        )
        session.merge(mark)
        session.commit()

def get_prior_eod_mark(instrument_id: str, mark_date: date = None):
    if mark_date is None:
        mark_date = date.today()
    with Session(engine) as session:
        return session.query(EODMark).filter(
            EODMark.instrument_id == instrument_id,
            EODMark.mark_date < mark_date
        ).order_by(EODMark.mark_date.desc()).first()
'''

open('src/database/eod_marks.py', 'w').write(eod_marks)
print('eod_marks.py written')