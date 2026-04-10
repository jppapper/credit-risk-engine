import numpy as np
import datetime
from scipy.optimize import brentq

class BondAnalytics:
    def __init__(self, instrument_id: str, start_date: str, maturity_date: str, coupon_bps: float, notional: float, payment_frequency: int=2, day_count_convention: str="A/360"):
        # TODO: implement day count convention in accrued interest
        self.instrument_id = instrument_id
        self.start_date = start_date
        self.maturity_date = maturity_date
        self.coupon_bps = coupon_bps
        self.notional = notional
        self.payment_frequency = payment_frequency
        self.day_count_convention = day_count_convention

    def _build_payment_dates(self, start_date=None, end_date=None) -> list:
        if start_date is None:
            start_date = datetime.date.today()
        if end_date is None:
            end_date = datetime.date.fromisoformat(self.maturity_date)
        payment_dates = []
        current_date = start_date
        while current_date < end_date:
            # TODO: use calendar-based quarter dates
            current_date = current_date + datetime.timedelta(days=90)
            payment_dates.append(current_date)
        return payment_dates

    def calc_discount_factors(self, rate: float, end_date: str):
        start_date = datetime.date.today()
        end_date = datetime.date.fromisoformat(end_date)
        t= (end_date - start_date).days / 365
        discount_factor = np.exp(-rate*t)
        return discount_factor
    
    def calc_dirty_price(self, rate: float):
        payment_dates = self._build_payment_dates( )
        payment = 0
        for date in payment_dates:
            df = self.calc_discount_factors(rate, date.isoformat())
            payment += (self.coupon_bps/10000) * self.notional * 1/self.payment_frequency * df
        final_df = self.calc_discount_factors(rate, self.maturity_date)
        payment += self.notional * final_df
        dirty_price = 100*payment/self.notional
        return dirty_price

    def calc_accrued_interest(self):
        payment_dates = self._build_payment_dates()
        last_payment_date = datetime.date.fromisoformat(self.start_date)
        for date in reversed(payment_dates):
            if date <= datetime.date.today():
                last_payment_date = date
                break
        payment_days = (datetime.date.today() - last_payment_date).days
        days_in_period = 360/self.payment_frequency
        accrued_interest = (payment_days/days_in_period) * (self.coupon_bps/10000) * 1/self.payment_frequency * self.notional
        return accrued_interest
    
    def calc_clean_price(self, rate: float):
        clean_price = self.calc_dirty_price(rate) - self.calc_accrued_interest()
        return clean_price
    
    def calc_ytm(self, market_price: float):
        def ytm_solver(rate: float):
            return self.calc_dirty_price(rate) - market_price
        return brentq(ytm_solver, 0.0001, 0.5)
    
    def calc_dv01(self, rate: float):
        up_upfront = self.calc_dirty_price(rate + .0001)
        down_upfront = self.calc_dirty_price(rate - .0001)
        dv01 = (up_upfront - down_upfront)/2
        return dv01
    
    def calc_duration(self, rate: float):
        dirty_price = self.calc_dirty_price(rate)
        price_up = self.calc_dirty_price(rate + .0001)
        price_down = self.calc_dirty_price(rate - .0001)
        duration = -(1/dirty_price) * (price_up - price_down) / (2 * 0.0001)
        return duration
    
    def calc_convexity(self, rate: float):
        dirty_price = self.calc_dirty_price(rate)
        price_up = self.calc_dirty_price(rate + .0001)
        price_down = self.calc_dirty_price(rate - .0001)
        convexity = (1/dirty_price) * (price_up - 2*dirty_price + price_down) / (0.0001**2)
        return convexity
    
    def calc_z_spread(self, rate: float, market_price: float):
        def z_spread_solver(z_spread):
            return self.calc_dirty_price(rate+z_spread) - market_price
        return brentq(z_spread_solver, 0.0001, 0.5)

    def calc_carry(self):
        carry = (self.coupon_bps / 10000) * self.notional/360
        return carry