"""
URL configuration for HRAgentUI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.homepage),
    path('about/',views.about),
    path('faq/',views.faq_agent),
    path('email-onboarding/',views.onboarding),
    path('candidate-notes/',views.candidate_notes),
    path('summarize-notes/', views.summarize_notes, name='summarize_notes'),
    path('process_form/', views.process_form, name='process_form'),
    path('onboarding-submit/',views.onboarding_submit, name='onboarding_submit'),
]
