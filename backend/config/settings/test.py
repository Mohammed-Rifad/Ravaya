from .base import *  # noqa: F403

DEBUG = False
# Fast, insecure hashing: only acceptable because test users are throwaway.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
