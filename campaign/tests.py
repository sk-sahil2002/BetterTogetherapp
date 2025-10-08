from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Campaign, Donation
from core.models import Category, Country

User = get_user_model()


class DonationOrderingTestCase(TestCase):
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.country = Country.objects.create(name='Test Country')
        self.category = Category.objects.create(name='Test Category')
        
        self.campaign = Campaign.objects.create(
            title='Test Campaign',
            description='Test Description',
            user=self.user,
            category=self.category,
            goal=1000,
            location='Test Location',
            deadline=timezone.now().date() + timedelta(days=30),
            image='test.jpg'
        )
    
    def test_donation_ordering_by_date_and_id(self):
        """Test that donations are ordered by date and id fields"""
        # Create donations with different dates
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)
        
        donation1 = Donation.objects.create(
            campaign=self.campaign,
            fullname='Donor 1',
            email='donor1@example.com',
            country='Test Country',
            postal_code='12345',
            donation=100,
            date=day_before
        )
        
        donation2 = Donation.objects.create(
            campaign=self.campaign,
            fullname='Donor 2',
            email='donor2@example.com',
            country='Test Country',
            postal_code='12345',
            donation=200,
            date=yesterday
        )
        
        donation3 = Donation.objects.create(
            campaign=self.campaign,
            fullname='Donor 3',
            email='donor3@example.com',
            country='Test Country',
            postal_code='12345',
            donation=300,
            date=today
        )
        
        # Test ordering
        donations = Donation.objects.filter(campaign=self.campaign).order_by('-date', '-id')
        
        # Should be ordered by date descending (most recent first), then by id
        self.assertEqual(donations[0], donation3)
        self.assertEqual(donations[1], donation2)
        self.assertEqual(donations[2], donation1)
    
    def test_same_day_donations_ordering(self):
        """Test that donations on the same day are ordered by ID (most recent first)"""
        today = timezone.now().date()
        
        # Create donations on the same day
        donation1 = Donation.objects.create(
            campaign=self.campaign,
            fullname='Donor 1',
            email='donor1@example.com',
            country='Test Country',
            postal_code='12345',
            donation=100,
            date=today
        )
        
        donation2 = Donation.objects.create(
            campaign=self.campaign,
            fullname='Donor 2',
            email='donor2@example.com',
            country='Test Country',
            postal_code='12345',
            donation=200,
            date=today
        )
        
        donation3 = Donation.objects.create(
            campaign=self.campaign,
            fullname='Donor 3',
            email='donor3@example.com',
            country='Test Country',
            postal_code='12345',
            donation=300,
            date=today
        )
        
        # Test ordering - should be by ID descending (most recent first)
        donations = Donation.objects.filter(campaign=self.campaign).order_by('-date', '-id')
        
        # Since UUIDs are random, we just verify that all donations are present
        # and that they're ordered by date (all same day) and then by ID
        self.assertEqual(len(donations), 3)
        self.assertEqual(donations[0].date, today)
        self.assertEqual(donations[1].date, today)
        self.assertEqual(donations[2].date, today)
        
        # Verify that IDs are in descending order
        self.assertGreater(donations[0].id, donations[1].id)
        self.assertGreater(donations[1].id, donations[2].id)
    
    def test_campaign_detail_view_ordering(self):
        """Test that CampaignDetailView returns donations in correct order"""
        from django.test import Client
        from django.urls import reverse
        
        # Create test donations
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        donation1 = Donation.objects.create(
            campaign=self.campaign,
            fullname='Old Donor',
            email='old@example.com',
            country='Test Country',
            postal_code='12345',
            donation=100,
            date=yesterday,
            approved=True
        )
        
        donation2 = Donation.objects.create(
            campaign=self.campaign,
            fullname='Recent Donor',
            email='recent@example.com',
            country='Test Country',
            postal_code='12345',
            donation=200,
            date=today,
            approved=True
        )
        
        # Test the view
        client = Client()
        response = client.get(reverse('campaign:campaign-detail', kwargs={'pk': self.campaign.id}))
        
        self.assertEqual(response.status_code, 200)
        donations = response.context['donations']
        
        # Most recent donation should be first
        self.assertEqual(donations[0], donation2)
        self.assertEqual(donations[1], donation1)
