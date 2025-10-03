from django.conf.urls.static import static
from django.urls import path, include

from qonty import settings
from .views import *

app_name = "core"

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('categories', CategoryListView.as_view(), name="categories"),
    path('campaigns-by-category/<int:pk>', CampaignsByCategoryView.as_view(), name="campaigns-by-category"),
    path('how-it-works/', HowItWorksView.as_view(), name='how-it-works'),
    path('about/', TemplateView.as_view(template_name='static_pages/about.html'), name='about'),
    path('terms/', TemplateView.as_view(template_name='static_pages/terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='static_pages/privacy.html'), name='privacy'),
    path('help/', TemplateView.as_view(template_name='static_pages/help.html'), name='help'),
    path('success-stories/', TemplateView.as_view(template_name='static_pages/success.html'), name='success-stories'),
    path('guidelines/', TemplateView.as_view(template_name='static_pages/guidelines.html'), name='guidelines'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
