from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render

from campaign.models import Campaign, Donation


class DashboardView(View):
    template_name = "dashboard/home.html"

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Get date 30 days ago
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Get user campaigns
        user_campaigns = Campaign.objects.filter(user=self.request.user)
        
        # Get daily donations RECEIVED on user's campaigns for last 30 days
        daily_donations = Donation.objects.filter(
            campaign__user=self.request.user,
            date__gte=thirty_days_ago
        ).annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            total=Sum('donation'),
            count=Count('id')
        ).order_by('day')

        # Get daily donations GIVEN by the user (by email) for last 30 days
        daily_given = Donation.objects.filter(
            email=self.request.user.email,
            date__gte=thirty_days_ago
        ).annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            total=Sum('donation'),
            count=Count('id')
        ).order_by('day')
        
        # Prepare chart data
        dates = []
        amounts = []
        counts = []
        
        current_date = thirty_days_ago.date()
        end_date = timezone.now().date()
        
        # Create lookup dictionary
        donations_dict = {
            d['day'].strftime('%Y-%m-%d'): {'total': d['total'], 'count': d['count']}
            for d in daily_donations
        }
        given_dict = {
            d['day'].strftime('%Y-%m-%d'): {'total': d['total'], 'count': d['count']}
            for d in daily_given
        }

        while current_date <= end_date:
            dates.append(current_date.strftime('%Y-%m-%d'))
            current_datetime = timezone.make_aware(
                timezone.datetime.combine(current_date, timezone.datetime.min.time())
            )
            key = current_datetime.strftime('%Y-%m-%d')
            day_data = donations_dict.get(key, {'total': 0, 'count': 0})
            given_data = given_dict.get(key, {'total': 0, 'count': 0})
            amounts.append(float(given_data['total'] or 0))
            counts.append(given_data['count'])
            current_date += timedelta(days=1)

        # Get campaigns the user has donated to
        donated_campaigns = Campaign.objects.filter(
            donation__email=self.request.user.email
        ).distinct().select_related('user').prefetch_related('donation_set').order_by('-donation__date')[:6]

        context = {
            "active_campaigns": user_campaigns.filter(status="active").count(),
            # Total raised on user's campaigns (received)
            "total_raised": Donation.objects.filter(
                campaign__user=self.request.user
            ).aggregate(Sum("donation"))["donation__sum"] or 0,
            # My donations given (by email)
            "my_given_total": Donation.objects.filter(email=self.request.user.email).aggregate(Sum("donation"))["donation__sum"] or 0,
            "my_given_count": Donation.objects.filter(email=self.request.user.email).count(),
            # Campaigns the user has donated to
            "donated_campaigns": donated_campaigns,
            # Keep original dates but chart now shows given amounts
            "chart_dates": dates,
            "chart_amounts": amounts,
            "chart_counts": counts,
        }
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())


class CampaignListView(ListView):
    template_name = "dashboard/campaigns.html"
    context_object_name = "campaigns"
    paginate_by = 10

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_queryset(self):
        return (
            Campaign.objects.filter(user=self.request.user)
            .prefetch_related("donation_set")
            .order_by("-date")
        )


class DonationListView(ListView):
    template_name = "dashboard/donations.html"
    context_object_name = "donations"
    paginate_by = 10

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_queryset(self):
        return Donation.objects.filter(
            campaign__user=self.request.user
        ).select_related(
            'campaign'
        ).order_by('-date', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        donations = self.get_queryset()
        context.update({
            'total_donations': donations.count(),
            'total_amount': donations.aggregate(Sum('donation'))['donation__sum'] or 0,
            'approved_donations': donations.filter(approved=True).count(),
            'pending_donations': donations.filter(approved=False).count(),
        })
        return context
