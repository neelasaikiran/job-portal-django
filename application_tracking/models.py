from datetime import timezone
from django.db import models
from django.urls import reverse
from common.models import BaseModel
from accounts.models import User
from application_tracking.enums import ApplicationStatus, Employment_Type,Experience_Level,LocationTypeChoice
from django.db.models import Q 



# Create your models here.




class JobAdvert(BaseModel):
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    employment_type = models.CharField(max_length=55, choices=Employment_Type)
    experience_level = models.CharField(max_length=55, choices=Experience_Level)
    description = models.TextField()
    job_type = models.CharField(max_length=55, choices=LocationTypeChoice)
    location = models.CharField(max_length=255, null=True, blank=True)
    is_published =  models.BooleanField(default=True)
    deadline = models.DateField()
    skills = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    
    class Meta:
        ordering = ("-created_at",)
        
    def publish_advert(self) -> None:
        self.is_published = True
        self.save(update_fields=["is_published"])
    
    @property  
    def total_applicants(self):
        return self.applications.count()
    
    def get_absolute_url(self):
        return reverse("job_advert", kwargs={"advert_id": str(self.id)})
     

class JobApplication(BaseModel):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    portfolio_url = models.URLField()
    cv = models.FileField()
    status = models.CharField(max_length=20, choices=ApplicationStatus, default=ApplicationStatus.APPLIED)
    job_advert = models.ForeignKey(JobAdvert, on_delete=models.CASCADE, related_name="applications")
        
        
        
    
class JobAdvertQuerySet(models.Model):
    def active(self):
        return self.filter(is_published=True, deadline__gte=timezone.now().date())
    
    def search(self, keyword, location):
        query = Q()
        
        
        if keyword:
            query &= (
            Q(title__icontains=keyword) 
            |  Q(company_name__icontains=keyword) 
            |  Q(description__icontains=keyword)
            |  Q(skills__icontains=keyword)        
        )
        if location:
            query &= Q(location__icontains=location) 
        return self.active().filter(query)
    
            
        