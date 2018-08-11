from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
import json
from page import sparql_wrapper as spql_wrapper
from smart_selects.db_fields import ChainedForeignKey, ChainedManyToManyField
from django.contrib.postgres.fields import JSONField

# from django.dispatch import receiver
# import datetime
# from urllib.error import HTTPError
# from urllib.request import Request, urlopen
# from urllib.parse import urlencode
# from base64 import b64encode
# from django.db.models import Q

# Create your models here.


class Repository(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    repo_name = models.CharField(max_length=200)
    query_path = models.URLField(max_length=500)
    created_date = models.DateTimeField(default=timezone.now, editable=False)  # cannot edit via admin panel
    updated_date = models.DateTimeField(blank=True, editable=False)

    class Meta:  # Display in admin panel
        verbose_name = 'My Repository'
        verbose_name_plural = 'My Repositories'

    def save(self, *args, **kwargs):  # do something every time you save
        self.updated_date = timezone.now()
        super().save(*args, **kwargs)  # Call the "real" save() method.

    def __str__(self):
        return '%s <%s>' % (self.repo_name, self.query_path)

    # class Meta:
    #     verbose_name = 'My Repository'
    #     verbose_name_plural = 'My Repositories'


def save_repository(sender, instance, created, **kwargs):
    if created:
        sparql_class = 'SELECT DISTINCT ?class ?c_label ' \
                       + 'WHERE {' \
                       + '?property rdfs:domain ?class .' \
                       + 'optional{?class rdfs:label ?c_label}' \
                       + '}order by ?class'
        data_class = spql_wrapper.initial_model_api(sparql_class, instance.query_path)
        results = json.loads(data_class)
        for result in results['results']['bindings']:
            Domain.objects.create(domain_path=result.get('class').get('value'), author_id=instance.author_id,
                                  repository_query=instance)

        sparql_property = 'SELECT DISTINCT ?class ?c_label ?property ?p_label ' \
                          + 'WHERE {' \
                          + '?property rdfs:domain ?class .' \
                          + 'optional{?class rdfs:label ?c_label}' \
                          + 'optional{?property rdfs:label ?p_label}' \
                          + '}order by ?class'
        data_property = spql_wrapper.initial_model_api(sparql_property, instance.query_path)
        results = json.loads(data_property)
        for result in results['results']['bindings']:
            check_class = Domain.objects.filter(repository_query=instance.id).filter(
                domain_path=result.get('class').get('value')).first()
            Property.objects.create(property_path=result.get('property').get('value'), author_id=instance.author_id,
                                    domain_prop=check_class, repository_query=instance)


post_save.connect(save_repository, sender=Repository)


class Domain(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    domain_path = models.URLField(max_length=500)
    repository_query = models.ForeignKey(Repository, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return self.domain_path


class Property(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    property_path = models.URLField(max_length=500)
    domain_prop = models.ForeignKey(Domain, on_delete=models.CASCADE, blank=True, null=True)
    repository_query = models.ForeignKey(Repository, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return self.property_path


class Forcegraph(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    page_title = models.CharField(max_length=200)
    repository_query = models.ForeignKey(Repository, on_delete=models.CASCADE)
    domain_subject = ChainedForeignKey(
        Domain,
        chained_field='repository_query',
        chained_model_field='repository_query',
        show_all=False,
        auto_choose=True,
        sort=True
    )
    faceted_search = models.ManyToManyField(Property)
    # domain_subject = models.ForeignKey(Domain, on_delete=models.CASCADE)
    source = JSONField(blank=True, null=True, editable=False)
    result = JSONField(blank=True, null=True, editable=False)
    created_date = models.DateTimeField(
        default=timezone.now, editable=False)
    updated_date = models.DateTimeField(
        default=timezone.now, editable=False)
    published_date = models.DateTimeField(
        blank=True, null=True)

    class Meta:
        verbose_name = 'Graph Node-Link'
        verbose_name_plural = 'Graph Node-Links'

    def save(self, *args, **kwargs):  # do something every time you save
        if not self.pk:
            sparql_all = 'SELECT DISTINCT * WHERE { ?subject rdf:type <' + self.domain_subject.domain_path + '> .' \
                         + '?subject ?predicate ?object .' \
                         + 'optional{?subject rdfs:label ?s_label}' \
                         + 'optional{?predicate rdfs:label ?p_label}' \
                         + 'optional{?object rdfs:label ?o_label}' \
                         + 'filter(?object != owl:NamedIndividual)' \
                         + '}order by ?subject'  # filter(?object != owl:NamedIndividual && ?predicate != rdf:type)
            data = spql_wrapper.initial_model_api(sparql_all, self.repository_query.query_path)
            self.source = json.loads(data)
            self.updated_date = timezone.now()
            super().save(*args, **kwargs)  # Call the "real" save() method.
        else:
            self.updated_date = timezone.now()
            super().save(*args, **kwargs)  # Call the "real" save() method.

    def was_published_last(self):
        now = timezone.now()
        if self.published_date is not None:
            return self.published_date <= now

    was_published_last.admin_order_field = 'published_date'
    was_published_last.boolean = True
    was_published_last.short_description = 'Published ?'

    def __str__(self):
        return self.page_title


class Timelinegraph(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    page_title = models.CharField(max_length=200)
    repository_query = models.ForeignKey(Repository, on_delete=models.CASCADE)
    domain_subject = ChainedForeignKey(
        Domain,
        chained_field='repository_query',
        chained_model_field='repository_query',
        show_all=False,
        auto_choose=True,
        sort=True
    )
    date_marked = models.ForeignKey(Property, on_delete=models.CASCADE)
    # date_marked = ChainedForeignKey(
    #     Property,
    #     chained_field='domain_subject',
    #     chained_model_field='domain_prop',
    #     # related_name='date_marked',
    #     show_all=False,
    #     auto_choose=False,
    #     sort=True
    # )
    faceted_search = models.ManyToManyField(Property, related_name='faceted_search')
    # domain_subject = models.ForeignKey(Domain, on_delete=models.CASCADE)
    source = JSONField(blank=True, null=True, editable=False)
    result = JSONField(blank=True, null=True, editable=False)
    created_date = models.DateTimeField(
        default=timezone.now, editable=False)
    updated_date = models.DateTimeField(
        default=timezone.now, editable=False)
    published_date = models.DateTimeField(
        blank=True, null=True)

    class Meta:
        verbose_name = 'Graph Timeline'
        verbose_name_plural = 'Graph Timelines'

    def save(self, *args, **kwargs):  # do something every time you save
        if not self.pk:
            sparql_all = 'SELECT DISTINCT * WHERE { ?subject rdf:type <' + self.domain_subject.domain_path + '> .' \
                         + '?subject ?predicate ?object .' \
                         + 'optional{?subject rdfs:label ?s_label}' \
                         + 'optional{?predicate rdfs:label ?p_label}' \
                         + 'optional{?object rdfs:label ?o_label}' \
                         + 'filter(?object != owl:NamedIndividual)' \
                         + '}order by ?subject'  # filter(?object != owl:NamedIndividual && ?predicate != rdf:type)
            data = spql_wrapper.initial_model_api(sparql_all, self.repository_query.query_path)
            self.source = json.loads(data)
            self.updated_date = timezone.now()
            super().save(*args, **kwargs)  # Call the "real" save() method.
        else:
            self.updated_date = timezone.now()
            super().save(*args, **kwargs)  # Call the "real" save() method.

    def was_published_last(self):
        now = timezone.now()
        if self.published_date is not None:
            return self.published_date <= now

    was_published_last.admin_order_field = 'published_date'
    was_published_last.boolean = True
    was_published_last.short_description = 'Published ?'

    def __str__(self):
        return self.page_title
