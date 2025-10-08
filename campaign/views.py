from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.db.models import Q, Sum
from django.views.generic import CreateView, DetailView, ListView, View
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string

from core.models import Country
from .forms import *


class CampaignListView(ListView):
    model = Campaign
    template_name = "campaigns/list.html"
    context_object_name = "campaigns"
    paginate_by = 12  # Show 12 campaigns per page

    def get_queryset(self):
        queryset = Campaign.objects.prefetch_related("user").order_by('-date')
        
        # Handle search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('q', '')
        return context


@method_decorator(csrf_exempt, name='dispatch')
class CampaignCreateView(CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = "campaigns/create.html"
    success_url = "/"

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        # Make campaign available immediately
        self.object.status = "approved"
        self.object.is_active = True
        self.object.save()
        data = {"success": True, "target": self.get_success_url()}
        return JsonResponse(data)
        # return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        data = {
            "success": False,
            "errors": form.errors,
        }
        return JsonResponse(data, status=200)
        # return super(CampaignCreateView, self).form_invalid(form)

    # def get_form_kwargs(self):
    #     kwargs = super(CampaignCreateView, self).get_form_kwargs()
    #     kwargs.update({'user': self.request.user})
    #     kwargs.update({'status': 'pending'})
    #     return kwargs


class CampaignDetailView(DetailView):
    model = Campaign
    template_name = "campaigns/details.html"
    context_object_name = "campaign"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.get_object()
        
        # Get donation statistics
        donations = campaign.donation_set.filter(approved=True)
        total_raised = donations.aggregate(Sum('donation'))['donation__sum'] or 0
        total_donors = donations.count()
        
        # Calculate progress percentage
        progress_percentage = (total_raised / campaign.goal * 100) if campaign.goal > 0 else 0
        
        context.update({
            'total_raised': total_raised,
            'total_donors': total_donors,
            'progress_percentage': min(100, progress_percentage),  # Cap at 100%
            'donations': donations.order_by('-date', '-id')[:10],  # Get latest 10 donations, with id as tiebreaker
            'share_url': self.request.build_absolute_uri(),  # Full URL for sharing
        })
        return context


@method_decorator(csrf_exempt, name='dispatch')
class DonationView(CreateView):
    model = Donation
    template_name = "campaigns/make-donation.html"
    form_class = DonationForm
    
    def dispatch(self, request, *args, **kwargs):
        # Get campaign and verify it exists and is active
        self.campaign = get_object_or_404(
            Campaign.objects.select_related('user'),
            id=kwargs['pk'],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get donation statistics
        donations = self.campaign.donation_set.filter(approved=True)
        total_raised = donations.aggregate(Sum('donation'))['donation__sum'] or 0
        total_donors = donations.count()
        
        # Calculate progress percentage
        progress_percentage = (total_raised / self.campaign.goal * 100) if self.campaign.goal > 0 else 0

        context.update({
            'campaign': self.campaign,
            'countries': Country.objects.all(),
            'total_raised': total_raised,
            'total_donors': total_donors,
            'progress_percentage': min(100, progress_percentage),
            'min_donation': 5,  # Minimum donation amount
            'recent_donations': donations.order_by('-date', '-id')[:5],
            "percentage": int(progress_percentage),
        })
        return context

    def form_valid(self, form):
        donation = form.save(commit=False)
        
        # Set additional fields
        donation.campaign = self.campaign
        donation.date = now().date()  # Use date() to get only the date part
        donation.approved = True
        
        # Note: Donation model does not have a FK to user; use email/fullname already set by the form.
        
        # Validate minimum donation
        if donation.donation < 5:
            messages.error(self.request, 'Minimum donation amount is ₹5')
            return self.form_invalid(form)
            
        donation.save()
        # Send a thank-you email (best-effort)
        try:
            subject = 'Thank you for your donation to %s' % self.campaign.title
            message = (
                'Hi %s,\n\n'
                'Thank you for donating ₹%s to %s. Your support means a lot!\n\n'
                'Regards,\nBetterTogether'
            ) % (donation.fullname, donation.donation, self.campaign.title)
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@bettertogether.local'
            send_mail(subject, message, from_email, [donation.email], fail_silently=True)
        except Exception:
            pass

        # Redirect with a query param to trigger success popup reliably
        return redirect(f"{reverse_lazy('campaign:campaign-detail', kwargs={'pk': self.campaign.id})}?donation=success")

    def form_invalid(self, form):
        messages.error(
            self.request, 
            'Please correct the errors below.'
        )
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.is_authenticated:
            # Pre-fill form with user data
            kwargs['initial'] = {
                'fullname': self.request.user.get_full_name(),
                'email': self.request.user.email,
                'country': self.request.user.country.name if hasattr(self.request.user, 'country') and hasattr(self.request.user.country, 'name') else None
            }
        return kwargs


class LoadMoreDonationsView(View):
    """AJAX view to load more donations for a campaign"""
    
    def get(self, request, pk):
        try:
            campaign = get_object_or_404(Campaign, id=pk)
            offset = int(request.GET.get('offset', 0))
            limit = int(request.GET.get('limit', 10))
            
            # Get donations with offset and limit
            donations = campaign.donation_set.filter(
                approved=True
            ).order_by('-date', '-id')[offset:offset + limit]
            
            # Render the donation items as HTML
            donation_html = render_to_string('campaigns/partials/donation_item.html', {
                'donations': donations
            })
            
            # Check if there are more donations
            total_donations = campaign.donation_set.filter(approved=True).count()
            has_more = (offset + limit) < total_donations
            
            return JsonResponse({
                'success': True,
                'html': donation_html,
                'has_more': has_more,
                'next_offset': offset + limit,
                'total_donations': total_donations
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
