from django.test.client import Client
import pytest
from accounts.models import User
from django.contrib.auth.hashers import make_password


@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user_instance():
    return User.objects.create(
        email ="randomabc@gmail.com",
        password = make_password("abcd")
    )
    
@pytest.fixture 
def auth_user_password() -> str:
    """ Returns the password needed for authentication """ 
    return "abcd"
    
@pytest.fixture
def authenticate_user_client(client : Client, user_instance : User,auth_user_password : str) -> tuple[Client, User]:
    """Authenticate a client"""
    client.login(email=user_instance.email, password=auth_user_password)
    return client, user_instance

    
