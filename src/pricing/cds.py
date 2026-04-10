import numpy as np
import datetime

class CDSAnalytics:
    def __init__(self, instrument_id: str, maturity_date: str, coupon_bps: float, notional: float, recovery_rate: float = 0.40):
        self.instrument_id = instrument_id
        self.maturity_date = maturity_date
        self.coupon_bps = coupon_bps
        self.notional = notional
        self.recovery_rate = recovery_rate

    def calc_hazard_rate(self, spread_bps: float):
        hazard_rate = (spread_bps/10000)/(1-self.recovery_rate)
        return hazard_rate
    
    def calc_survival_probability(self, hazard_rate: float, end_date: str):
        start_date = datetime.date.today()
        end_date = datetime.date.fromisoformat(end_date)
        t= (end_date - start_date).days / 365
        survival_probability = np.exp(-hazard_rate*t)
        return survival_probability
    
    def calc_discount_factors(self, rate: float, end_date: str):
        start_date = datetime.date.today()
        end_date = datetime.date.fromisoformat(end_date)
        t= (end_date - start_date).days / 365
        discount_factor = np.exp(-rate*t)
        return discount_factor

    def _build_payment_dates(self, end_date: str) -> list:
        payment_dates = []
        start_date = datetime.date.today()
        end_date = datetime.date.fromisoformat(end_date)
        current_date = start_date
        while current_date < end_date:
            current_date = current_date + datetime.timedelta(days=90)
            payment_dates.append(current_date)
        return payment_dates        


    def calc_protection_leg(self, par_coupon: float, end_date: str, rate: float):
        hazard_rate = self.calc_hazard_rate(par_coupon)
        payment_dates = self._build_payment_dates(end_date)
        protection_leg = 0
        prev_survival_rate = 1
        for date in  payment_dates:
            current_survival_rate = self.calc_survival_probability(hazard_rate, date.isoformat())
            default_probability = prev_survival_rate - current_survival_rate
            df = self.calc_discount_factors(rate, date.isoformat())
            protection_leg += self.notional * (1 - self.recovery_rate) * default_probability * df
            prev_survival_rate = current_survival_rate 
        return protection_leg
    
    def calc_premium_leg(self, par_coupon: float, end_date: str, rate: float):
        hazard_rate = self.calc_hazard_rate(par_coupon)
        payment_dates = self._build_payment_dates(end_date)
        premium_leg = 0
        for date in payment_dates:
            current_survival_rate = self.calc_survival_probability(hazard_rate, date.isoformat())
            df = self.calc_discount_factors(rate, date.isoformat())
            premium_leg += self.notional * current_survival_rate * df * (self.coupon_bps / 10000) * 0.25
        return premium_leg
    
    def calc_upfront(self, par_coupon: float, end_date: str, rate: float):
        protection_leg = self.calc_protection_leg(par_coupon, end_date, rate)
        premium_leg = self.calc_premium_leg(par_coupon, end_date, rate)
        upfront = protection_leg - premium_leg
        return(upfront)
    
    def calc_cs01(self, par_coupon: float, end_date: str, rate: float):
        up_upfront = self.calc_upfront(par_coupon + 1, end_date, rate)
        down_upfront = self.calc_upfront(par_coupon - 1, end_date, rate)
        cs01 = (up_upfront - down_upfront)/2
        return cs01
    
    def calc_ir01(self, par_coupon: float, end_date: str, rate: float):
        up_upfront = self.calc_upfront(par_coupon, end_date, rate + .0001)
        down_upfront = self.calc_upfront(par_coupon, end_date, rate - .0001)
        ir01 = (up_upfront - down_upfront)/2
        return ir01
    
    def calc_jump_to_default(self, par_coupon: float, end_date: str, rate: float):
        upfront = self.calc_upfront(par_coupon, end_date, rate)
        protection_payment = self.notional * (1 - self.recovery_rate)
        jump_to_default = protection_payment - upfront
        return jump_to_default
    
    def calc_carry(self, par_coupon: float):
        carry = ((self.coupon_bps - par_coupon) / 10000) * self.notional * 1/360
        return carry
    


