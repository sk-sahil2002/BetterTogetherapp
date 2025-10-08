from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def div(value, arg):
    """Divides the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def progress_percentage(campaign):
    """Calculates the progress percentage of a campaign"""
    try:
        if campaign.goal <= 0:
            return 0
        
        total_raised = campaign.donation_set.filter(approved=True).aggregate(
            Sum('donation')
        )['donation__sum'] or 0
        
        percentage = (total_raised / campaign.goal) * 100
        return min(100, round(percentage, 1))
    except (ValueError, ZeroDivisionError, AttributeError):
        return 0

@register.filter
def total_raised(campaign):
    """Gets the total amount raised for a campaign"""
    try:
        total = campaign.donation_set.filter(approved=True).aggregate(
            Sum('donation')
        )['donation__sum'] or 0
        return total
    except (ValueError, AttributeError):
        return 0 