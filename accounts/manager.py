from django.contrib.auth.base_user import BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Customer User model Manager where email is the unique identifier 
    """
    def create_user(self, email, password, **extra_fields):
        """
        create and save a User with the given email and password
        """
        if not email:
            raise ValueError("Email must be set")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    
    
    def create_superuser(self, email, password, **extra_fields):
        """
        create and save a superuser with the given mail and pasword
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        user = self.create_superuser(email, password, **extra_fields)
        user.save()
        
        

        
        
        