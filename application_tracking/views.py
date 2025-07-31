from datetime import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from application_tracking.enums import ApplicationStatus
from application_tracking.forms import JobAdvertForm, JobApplicationForm 
from application_tracking.models import JobAdvert, JobApplication
from django.core.paginator import Paginator
from django.utils import timezone
from common.tasks import send_email
from django.db.models import Q



@login_required
def create_advert(request: HttpRequest):
    form = JobAdvertForm(request.POST or None)
    
    if form.is_valid():
        instance: JobAdvert = form.save(commit=False)
        instance.created_by = request.user
        instance.save()
        
        messages.success(request, "Advert created. You can now receive applications.")
        return redirect(instance.get_absolute_url())  # Ensure this is defined in the JobAdvert model
    
    context = {
        "job_advert_form": form,
        "title": "Create a new Advert",
        "btn_text": "Create Advert"
    }
    return render(request, 'create_advert.html', context)



def get_advert(request: HttpRequest, advert_id):
    form = JobApplicationForm()
    job_advert = get_object_or_404(JobAdvert, pk=advert_id)
    context = {
        "job_advert": job_advert,
        "application_form" :form
    }  
    return render(request, "advert.html", context)


# Placeholder views for future development
@login_required
def list_adverts(request: HttpRequest):
    """List all published job adverts."""
    active_jobs = JobAdvert.objects.active()
    
    paginator = Paginator(active_jobs,10)
    requested_page = request.GET.get('page')
    paginated_adverts = paginator.get_page(requested_page) 
    
    context ={
        "job_adverts" : paginated_adverts,      
    }
    # return render(request, "application_tracking/home.html", context)
    return render(request, "home.html", context)
    

@login_required
def update_advert(request: HttpRequest, advert_id):
    """Update an existing job advert."""
    advert = get_object_or_404(JobAdvert, pk=advert_id)
    if request.user !=advert.created_by:
        return HttpResponseForbidden("You can only update an advert created by you")
    
    form = JobAdvertForm(request.POST or None, instance=advert)
    
    if form.is_valid():
        instance : JobAdvert = form.save(commit=False)
        instance.save()
        messages.success(request, "Adverted updated successfully.")
        return redirect(instance.get_absolute_url())
    
    context = {
        "job_advert_form" : form,
        "btn_text" : "Update Advert"
        
    }
    return render(request, "create_advert.html", context)


@login_required
def delete_advert(request: HttpRequest, advert_id):
    """Delete an existing job advert."""
    advert = get_object_or_404(JobAdvert, pk=advert_id)
    if request.user !=advert.created_by:
        return HttpResponseForbidden("You can only update an advert created by you")
    
    advert.delete()
    messages.success(request, "Advert deleted successfully.")
    return redirect('my_jobs')
    

@login_required
def apply(request: HttpRequest, advert_id):
    """Apply for a job advert."""
    advert = get_object_or_404(JobAdvert, pk=advert_id)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data["email"]
            if advert.applications.filter(email__iexact=email).exists():
                messages.error(request, "You have already applied for this position")
                return redirect('job_advert', advert_id=advert_id)

            application = form.save(commit=False)
            application.job_advert = advert
            application.save()

            messages.success(request, "Application submitted successfully..!")
            return redirect('job_advert', advert_id=advert_id)
    else:
        form = JobApplicationForm()

    context = {
        "job_advert": advert,
        "application_form": form
    }
    return render(request, "advert.html", context)


@login_required
def my_applications(request: HttpRequest):
    """View user's submitted applications."""
    user : User = request.user
    applications = JobApplication.objects.filter(email=user.email)
    paginator = Paginator(applications,5)
    
    requested_page = request.GET.get('page')
    paginated_applications = paginator.get_page(requested_page)
    
    context = {
        "my_applications" : paginated_applications
    } 
    return render(request, "my_applications.html", context)


@login_required
def my_jobs(request: HttpRequest):
    """View jobs posted by the logged-in user."""
    user: User = request.user
    jobs = JobAdvert.objects.filter(created_by=user)
    paginator = Paginator(jobs,5)
    requested_page = request.GET.get("page")
    paginated_jobs = paginator.get_page(requested_page)
    
    context ={
        "my_jobs" : paginated_jobs,
        "current_date" : timezone.now().date()
    }
    return render(request, "my_jobs.html", context)


@login_required
def advert_applications(request: HttpRequest, advert_id):
    advert : JobAdvert = get_object_or_404(JobAdvert, pk=advert_id)
    if request.user != advert.created_by:
        return HttpResponseForbidden("You can only see applications for an advert created by you")
    
    applications = advert.applications.all()
    # applications = JobApplication.objects.filter(job_advert=advert.id)
    paginator = Paginator(applications, 10)
    requested_page = request.GET.get("page")
    paginated_applications = paginator.get_page(requested_page)
    
    context = {
        "applications" : paginated_applications,
        "advert"  : advert
    } 
    return render(request, "advert_applications.html", context)
  
  
@login_required
def decide(request:HttpRequest, job_application_id):
    job_application : JobApplication = get_object_or_404(JobApplication, pk=job_application_id)
    
    if request.user != job_application.job_advert.created_by:
        return HttpResponseForbidden("You can only decide on an advert created ")
    
    if request.method == "POST":
        status = request.POST.get("status")
        job_application.status = status
        job_application.save(update_fields=["status"])
        messages.success(request, "Application status updated to {status}")
        
        if status == ApplicationStatus.REJECTED:
            context = {
                "applicant_name" : job_application.name,
                "job_title" : job_application.job_advert.title,
                "company_name" : job_application.job_advert.company_name
            }
            send_email(
                f"Application Outcome for {job_application.job_advert.title}",
                [job_application.email],
                "emails/job_application_update.html",
                context
                
            )
        
        return redirect('advert_applications', advert_id=job_application.job_advert.id)


def search(request:HttpRequest):
    keyword = request.GET.get('keyword')
    location = request.GET.get('location')
    
    # query = Q()
    # if keyword:
    #     query &= (
    #         Q(title__icontains=keyword) 
    #         |  Q(company_name__icontains=keyword) 
    #         |  Q(description__icontains=keyword)
    #         |  Q(skills__icontains=keyword)        
    #     )
    
    # if location:
    #     query &= Q(location__icontains=location) 
    
    # active_jobs = JobAdvert.objects.filter(is_published=True, deadline__gte=timezone.now().date())
    
    result = JobAdvert.objects.search(keyword, location)
    paginator = Paginator(result,10)
    requested_page = request.GET.get('page')
    paginated_adverts = paginator.get_page(requested_page)
    
    context = {
        'job_adverts' : paginated_adverts
    }
    return render(request, "home.html", context)

