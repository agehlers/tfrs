"""
    REST API Documentation for the NRS TFRS Credit Trading Application

    The Transportation Fuels Reporting System is being designed to streamline compliance reporting for transportation fuel suppliers in accordance with the Renewable & Low Carbon Fuel Requirements Regulation.

    OpenAPI spec version: v1
        

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from django.db import models


class CurrentUserViewModel(models.Model):
    given_name = models.CharField(max_length=255, blank=True, null=True)
    surname = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField()
    user_roles = models.ManyToManyField(
        'UserRole',
        related_name='CurrentUserViewModeluser_roles',
        blank=True)
    sm_authorization_id = models.CharField(max_length=255, blank=True, null=True)
    sm_authorization_directory = models.CharField(max_length=255, blank=True,
                                                null=True)

    class Meta:
        abstract = True
