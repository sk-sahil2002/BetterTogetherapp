from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView, UpdateView, CreateView
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib import messages
from django.urls import reverse_lazy

from core.models import Category
from dashboard.mixins import SuperUserRequiredMixin
from campaign.models import Campaign, Donation, CampaignStatusChoices
from campaign.forms import CampaignForm
from accounts.models import User
from core.forms import CategoryForm


class AdminDashboardView(SuperUserRequiredMixin, View):
    def get(self, request):
        # Get date 30 days ago
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Get daily donations for last 30 days
        daily_donations = (
            Donation.objects.filter(date__gte=thirty_days_ago, approved=True)
            .annotate(day=TruncDay("date"))
            .values("day")
            .annotate(total=Sum("donation"), count=Count("id"))
            .order_by("day")
        )

        # Get latest members
        latest_members = User.objects.select_related("country").order_by(
            "-date_joined"
        )[:4]

        # Get recent campaigns
        recent_campaigns = Campaign.objects.select_related("user").order_by("-date")[:4]

        # Prepare chart data
        dates = []
        amounts = []
        counts = []

        current_date = thirty_days_ago.date()
        end_date = timezone.now().date()

        # Create lookup dictionary
        donations_dict = {
            d["day"].strftime("%Y-%m-%d"): {"total": d["total"], "count": d["count"]}
            for d in daily_donations
        }
        
        while current_date <= end_date:
            dates.append(current_date.strftime("%Y-%m-%d"))
            # Convert current_date to datetime for dictionary lookup
            current_datetime = timezone.make_aware(
                datetime.combine(current_date, datetime.min.time())
            )
            day_data = donations_dict.get(current_datetime.strftime("%Y-%m-%d"), {"total": 0, "count": 0})
            amounts.append(float(day_data["total"] or 0))
            counts.append(day_data["count"])
            current_date += timedelta(days=1)

        context = {
            "total_donations": Donation.objects.filter(approved=True).count(),
            "total_earnings": Donation.objects.filter(approved=True).aggregate(
                Sum("donation")
            )["donation__sum"]
            or 0,
            "total_members": User.objects.count(),
            "total_campaigns": Campaign.objects.count(),
            "latest_members": latest_members,
            "recent_campaigns": recent_campaigns,
            "chart_dates": dates,
            "chart_amounts": amounts,
            "chart_counts": counts,
        }
        
        # print(context)

        return render(request, "dashboard/admin/dashboard.html", context)


class AdminCampaignsView(SuperUserRequiredMixin, ListView):
    model = Campaign
    template_name = "dashboard/admin/campaigns.html"
    context_object_name = "campaigns"
    paginate_by = 10

    def get_queryset(self):
        return (
            Campaign.objects.select_related("user", "category")
            .prefetch_related("donation_set")
            .order_by("-date")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "total_campaigns": Campaign.objects.count(),
                "active_campaigns": Campaign.objects.filter(is_active=True).count(),
                "total_raised": Donation.objects.filter(approved=True).aggregate(
                    Sum("donation")
                )["donation__sum"]
                or 0,
            }
        )
        return context


class AdminDonationsView(SuperUserRequiredMixin, ListView):
    model = Donation
    template_name = "dashboard/admin/donations.html"
    context_object_name = "donations"
    paginate_by = 10

    def get_queryset(self):
        return Donation.objects.select_related("campaign").order_by("-date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "total_donations": Donation.objects.filter(approved=True).count(),
                "total_amount": Donation.objects.filter(approved=True).aggregate(
                    Sum("donation")
                )["donation__sum"]
                or 0,
                "pending_amount": Donation.objects.filter(approved=False).aggregate(
                    Sum("donation")
                )["donation__sum"]
                or 0,
                "admin_earnings": (
                    Donation.objects.filter(approved=True).aggregate(Sum("donation"))[
                        "donation__sum"
                    ]
                    or 0
                )
                * 0.05,  # 5% platform fee
            }
        )
        return context


class AdminCampaignEditView(SuperUserRequiredMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = "dashboard/admin/campaign-edit.html"
    success_url = reverse_lazy("admin_dashboard:campaigns")

    def form_valid(self, form):
        messages.success(self.request, "Campaign updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class AdminCampaignDeleteView(SuperUserRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        campaign_id = request.POST.get("id")
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            campaign.status = CampaignStatusChoices.DELETED
            campaign.save()
            messages.success(request, "Campaign deleted successfully!")
        except Campaign.DoesNotExist:
            messages.error(request, "Campaign not found!")
        return redirect("admin_dashboard:campaigns")


class AdminCategoriesView(SuperUserRequiredMixin, ListView):
    model = Category
    template_name = "dashboard/admin/categories.html"
    context_object_name = "categories"
    paginate_by = 10

    def get_queryset(self):
        return Category.objects.annotate(
            campaign_count=Count('campaign')
        ).order_by('-campaign_count')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm()
        return context


class AdminCategoryCreateView(SuperUserRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/admin/category-form.html"
    success_url = reverse_lazy('admin_dashboard:categories')
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class AdminCategoryUpdateView(SuperUserRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/admin/category-form.html"
    success_url = reverse_lazy('admin_dashboard:categories')
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)


class AdminCategoryDeleteView(SuperUserRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        category_id = request.POST.get('id')
        try:
            category = Category.objects.get(id=category_id)
            category.delete()
            messages.success(request, 'Category deleted successfully!')
        except Category.DoesNotExist:
            messages.error(request, 'Category not found!')
        return redirect('admin_dashboard:categories')


class AdminMembersView(SuperUserRequiredMixin, ListView):
    model = User
    template_name = "dashboard/admin/members.html"
    context_object_name = "members"
    paginate_by = 10

    def get_queryset(self):
        return User.objects.select_related("country").order_by("-date_joined")


class AdminMemberToggleView(SuperUserRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        member_id = request.POST.get('id')
        try:
            member = User.objects.get(id=member_id)
            member.is_active = not member.is_active
            member.save()
            messages.success(
                request, 
                f'Member {member.username} {"activated" if member.is_active else "deactivated"} successfully!'
            )
        except User.DoesNotExist:
            messages.error(request, 'Member not found!')
        return redirect('admin_dashboard:members')


class AdminMemberDeleteView(SuperUserRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        member_id = request.POST.get('id')
        try:
            member = User.objects.get(id=member_id)
            member.delete()
            messages.success(request, 'Member deleted successfully!')
        except User.DoesNotExist:
            messages.error(request, 'Member not found!')
        return redirect('admin_dashboard:members')