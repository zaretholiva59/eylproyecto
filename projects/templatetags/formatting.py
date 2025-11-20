from django import template

register = template.Library()

def _format_currency_pe(value):
    try:
        num = float(value or 0)
    except (TypeError, ValueError):
        num = 0.0
    s = f"{num:,.2f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')

@register.filter(name='currency_pe')
def currency_pe(value):
    return _format_currency_pe(value)

@register.filter(name='percent_pe')
def percent_pe(value, decimals=2):
    try:
        num = float(value or 0)
    except (TypeError, ValueError):
        num = 0.0
    try:
        d = int(decimals)
    except Exception:
        d = 2
    s = f"{num:.{d}f}"
    return s.replace('.', ',')