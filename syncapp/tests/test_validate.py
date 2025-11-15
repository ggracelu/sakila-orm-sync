from django.core.management import call_command
from django.test import TestCase

class ValidateCommandTest(TestCase):

    databases = {"default", "source"}

    def test_validate_runs_successfully(self):
        # should not raise errors
        call_command("validate")
