# -*- coding: utf-8 -*-
from odoo.tools import float_round

def round_tariff(value):
    return value #float_round(value, precision_digits=2)

def round_total(value):
    return float_round(value, precision_digits=0)
