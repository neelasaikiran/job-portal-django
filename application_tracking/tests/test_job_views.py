from accounts.tests.factories import UserFactory
from application_tracking.models import JobAdvert, JobApplication
from .factories import JobAdvertFactory, fake, JobApplicationFactory
from django.test.client import Client
from django.urls import reverse
from django.contrib.messages import get_messages
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


pytestmark = pytest.mark.django_db

def test_list_adverts(client:Client, user_instance):
    JobAdvertFactory.create_batch(20, created_by=user_instance, deadline=fake.future_date())
    JobAdvertFactory.create_batch(5, created_by=user_instance, deadline=fake.past_date())
    url = reverse("home")
    response = client.get(url)
    assert response.status_code == 302
    assert "job_adverts" in response.context
    
    
    paginated_adverts = response.context["job_adverts"]
    assert paginated_adverts.paginator.count == 20
    assert len(paginated_adverts.object_list) == 10
   


def test_retrive_an_adverts(client:Client, user_instance):
    advert = JobAdvertFactory(created_by=user_instance)
    url = reverse('job_advert', kwargs={"advert_id":advert.id})
    response = client.post(url)
    
    assert response.status_code == 200
    assert "job_advert"  in response.context
    assert "application_form" in response.context
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert messages[0].level_tag == 'success'
    assert JobAdvert.objects.count() == 0
    
    

def test_create_advert(authenticate_user_client):
    client, user = authenticate_user_client
    url = reverse('create_advert')
    
    requested_data = {
        "title" : "Title",
        "company_name" : "TCS",
        "employment_type" : 'Contract',
        "experience_level" : "Senior",
        "job_type" : "Remote",
        "deadline" : "2025-02-01",
        "skills" : "Python, Django",
        "description" : "Sample"
    }
    
    response =client.post(url, requested_data)
    assert response.status_code == 302
    
    assert JobAdvert.objects.count() == 1
    assert JobAdvert.objects.filter(created_by=user).count() == 1
    
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert messages[0].level_tag == 'success'
    assert "Email exists on the platform" in str(messages[0])

    
    
    
def test_delete_advert(authenticate_user_client):
    client, user = authenticate_user_client
    advert = JobAdvertFactory(created_by=user)
    url = reverse('delete_advert', kwargs={"advert_id":advert.id})
    response = client.post(url)
    
    assert response.status_code == 302
    assert response.url == reverse("my_jobs")
    
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert messages[0].level_tag == 'success'
    assert JobAdvert.objects.count() == 0
    
    
    
def test_edit_advert(authenticate_user_client):
    client, user = authenticate_user_client
    advert = JobAdvertFactory(created_by=user, title="RR", company_name="YY")
    url = reverse('update_advert', kwargs={"advert_id":advert.id})
    
    requested_data = {
        "title" : "Updated",
        "company_name" : "Sai Pvt Ltd",
        "employment_type" : "Contract",
        "experience_level" : 'Senior',
        "job_type" :"Remote",
        "deadline" : "2025-02-01",
        "skills" : "Python, Django",
        "description"  : "Sample" 
    }
    response = client.post(url, requested_data)
    assert response.status_code == 302
    assert response.url == reverse("job_advert",kwargs={"advert_id":advert.id})
    
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert messages[0].level_tag == 'success'
    
    advert.refresh_from_db()
    assert advert.title == requested_data['title']
    assert advert.company_name == requested_data['company_name']
    
 
    
def test_get_my_applications(authenticate_user_client):
    client, user = authenticate_user_client
    JobApplicationFactory.created_batch(5, email=user.email,  job_advert=JobAdvertFactory(
        created_by = UserFactory()
    ))
    JobApplicationFactory.created_batch(10, email="randomuser@gmail.com",  job_advert=JobAdvertFactory(
        created_by = UserFactory()
    ))
 
    url = reverse('my_applications')
    response = client.get(url)
    
    assert response.status_code == 200
    assert "my_applications" in response.context
    assert len(response.context["my_applications"].object_list) ==5
    
    
    
def test_get_my_jobs(authenticate_user_client):
    client, user = authenticate_user_client
    JobAdvertFactory.create_batch(5, created_by=user)
    JobAdvertFactory.create_batch(5, created_by=UserFactory())
    
    url = reverse('my_jobs')
    response = client.get(url)
    
    assert response.status_code == 200
    assert "my_jobs" in response.context
    assert len(response.context["my_jobs"].object_list) ==5
    

def test_apply_for_jobs(client:Client, user_instance):
    advert = JobAdvertFactory(created_by=user_instance)
    url = reverse("apply_for_job", kwargs={"advert_id" : advert.id} )
    
    cv = SimpleUploadedFile("sample.pdf", b"content")
    
    request_data = {
        "name" : 'Random name',
        "email" : "random@gmail.com",
        "portfolio_url" : "https://docs.djangoproject.com/en",
        "cv" : cv    
    }
    response = client.post(url, request_data)
    assert response.status_code == 302
    assert response.url == reverse("job_advert", kwargs={"advert_id": advert.id})
    
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert messages[0].level_tag == 'success'
    
    application = JobApplication.objects.filter(email=request_data["email"]).first()
    assert application.name == request_data["name"]
    assert application.cv.name.endswith(".pdf")
    
    application.cv.delete(save=False)
    
    
def test_apply_for_job_using_duplicate_email(client:Client, user_instance):
    advert = JobAdvertFactory(created_by=user_instance)
    application = JobApplicationFactory(job_advert=advert, email="abcabc1@gmail.com")
    url = reverse("apply_for_job", kwargs={"advert_id" : advert.id} )
    
    cv = SimpleUploadedFile("sample.pdf", b"content")
    
    request_data = {
        "name" : 'Random name',
        "email" : application.email,
        "portfolio_url" : "https://docs.djangoproject.com/en",
        "cv" : cv    
    }
    response = client.post(url, request_data)
    assert response.status_code == 302
    assert response.url == reverse("job_advert", kwargs={"advert_id": advert.id})
    
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert messages[0].level_tag == 'success'
    
    application = JobApplication.objects.filter(email=application.email, job_advert=advert.id).count() == 1
    assert application.name == request_data["name"]
    assert application.cv.name.endswith(".pdf")
    
    application.cv.delete(save=False)

