'''
Sitemap plugin for CKAN
'''

import ckan.plugins as p

from ckan.plugins.toolkit import config, url_for
from ckan.model import Session, Package
from flask import Blueprint, make_response
import ckan.logic as logic


from lxml import etree
from datetime import date
import json

import ckanext.sitemap.helpers as h

import logging

PURE_NS = "v1.dataset.pure.atira.dk"
PURE = "{%s}" % PURE_NS

PURE_CMNS = "v3.commons.pure.atira.dk"
CMNS = "{%s}" % PURE_CMNS

log = logging.getLogger(__file__)

def render_pure():
    # Consider adding validation here
    schema_file = '/usr/lib/ckan/default/src/ckanext-sitemap/ckanext/sitemap/dataset.xsd'
    xmlschema_doc = etree.parse(schema_file)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    # Whether to add extra elements.
    ADD_EXTRA_ELEMENTS = False
    context = {}

    #pkgs = Session.query(Package).filter(Package.type == 'dataset').filter(Package.private != True). \
    #    filter(Package.state == 'active').all()
    pkgs = logic.get_action('package_list')(context, {})

    root = etree.Element(PURE + "datasets", nsmap={'v1': PURE_NS, 'v3': PURE_CMNS})
    for pkg in pkgs:
        #pkg_dict = logic.get_action('package_show')(context, {'id': pkg.id})
        pkg_dict = logic.get_action('package_show')(context, {'id': pkg})

        # Filter out non-dataset, non-active packages
        if pkg_dict['type'] != 'dataset' or pkg_dict['state'] != 'active':
            continue

        #log.error(pkg_dict)
        dataset = etree.SubElement(root, PURE + 'dataset', attrib={'id': pkg_dict['id'], 'type': 'dataset'})

        # Title
        title = etree.SubElement(dataset, PURE + 'title')
        title.text = pkg_dict['title']

        # Description
        description = etree.SubElement(dataset, PURE + 'description')
        description.text = pkg_dict['notes']

        # Temporal Coverage:  Use only if it's defined
        if ADD_EXTRA_ELEMENTS:
            extentRange = h.getExtrasValue(pkg_dict, 'extent_range')
            if extentRange:
                (startDate, endDate) = h.getExtentParts(extentRange)
                temporalCoverage = etree.SubElement(dataset, PURE + 'temporalCoverage')
                start = etree.SubElement(temporalCoverage, PURE + 'from')
                fillDateFields(start, startDate)
                end = etree.SubElement(temporalCoverage, PURE + 'to')
                fillDateFields(end, endDate)

        # Geolocation:  We have to specify a polygon in Google Maps format.
        # Example would be nice; punt for now.

        # Persons: For now, we just populate with authors.
        if ADD_EXTRA_ELEMENTS:
            authors = h.getExtrasValue(pkg_dict, 'harvest-author')
            authors = json.loads(authors)
            persons = etree.SubElement(dataset, PURE + 'persons')
            for author in authors:
                person = etree.SubElement(persons, PURE + 'person', attrib={"id": author})
                personInner = etree.SubElement(person, PURE + 'person', attrib={"lookupId": author})
                # As a first pass, we put the entire author name into the "firstName" field.
                # personParts = h.getPersonParts(author)
                firstName = etree.SubElement(personInner, PURE + 'firstName')
                firstName.text = author
                role = etree.SubElement(person, PURE + 'role')
                role.text = 'creator'

        # DOI
        resource_url = h.getExtrasValue(pkg_dict, 'resource-url')
        if h.isDOI(resource_url):
            doi = etree.SubElement(dataset, PURE + 'DOI')
            doi.text = h.getDOISuffix(resource_url)

        # Available Date:  Could be just year, or year+month
        pubDate = h.getExtrasValue(pkg_dict, 'publication_date')
        dateParts = h.getDateParts(pubDate)
        availDate = etree.SubElement(dataset, PURE + 'availableDate')
        fillDateFields(availDate, dateParts)

        # Managing Organization
        managingOrg = h.getExtrasValue(pkg_dict, 'resource-support-organization')
        if not managingOrg:
            managingOrg = h.getExtrasValue(pkg_dict, 'metadata-support-organization')
        if not managingOrg:
            managingOrg = pkg_dict['organization']['title']
        org = etree.SubElement(dataset, PURE + 'managingOrganisation', attrib={'lookupId': managingOrg})

        # Publisher: Pure accepts only one publisher, so use the first one.
        publishers = h.getExtrasValue(pkg_dict, 'publisher-standard')
        publisher = json.loads(publishers)[0]
        org = etree.SubElement(dataset, PURE + 'publisher', attrib={'lookupId': publisher})

        # Link to resource homepage
        if ADD_EXTRA_ELEMENTS:
            links = etree.SubElement(dataset, PURE + 'links')
            link = etree.SubElement(links, PURE + 'link', attrib={'id': resource_url})
            description = etree.SubElement(link, PURE + 'description')
            descriptionText = etree.SubElement(description, CMNS + 'text')
            descriptionText.text = 'Resource Download Homepage'
            url = etree.SubElement(link, PURE + 'url')
            url.text = resource_url



    content = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='utf-8')

    #xmlschema.assertValid(root)

    # Add XML header
    headers = {'Content-Type': 'application/xml; charset=utf-8'}
    return make_response((content, 200, headers))


def fillDateFields(element, dateParts):
    year = etree.SubElement(element, CMNS + 'year')
    year.text = dateParts[0]
    if len(dateParts) > 1:
        month = etree.SubElement(element, CMNS + 'month')
        month.text = dateParts[1]
    if len(dateParts) > 2:
        day = etree.SubElement(element, CMNS + 'day')
        day.text = dateParts[2]


SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

XHTML_NS = "http://www.w3.org/1999/xhtml"

def render_sitemap():
    site_url = config.get('ckan.site_url')
    pkgs = Session.query(Package).filter(Package.type == 'dataset').filter(Package.private != True). \
        filter(Package.state == 'active').all()
    log.debug(pkgs)
    root = etree.Element("urlset", nsmap={None: SITEMAP_NS, 'xhtml': XHTML_NS})
    for pkg in pkgs:
        url = etree.SubElement(root, 'url')
        loc = etree.SubElement(url, 'loc')
        pkg_url = url_for('dataset.read', id=pkg.name)
        loc.text = site_url + pkg_url
        lastmod = etree.SubElement(url, 'lastmod')
        lastmod.text = pkg.metadata_modified.strftime('%Y-%m-%d')

    # Add XML header
    content = etree.tostring(root, pretty_print=True, encoding='unicode')
    content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
    headers = {'Content-Type': 'application/xml; charset=utf-8'}
    return make_response((content, 200, headers))


def testme():
    content = 'Test Me'
    headers = {'Content-Type': 'text/html; charset=utf-8'}
    return make_response((content, 200, headers))


class SitemapPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)

    def get_blueprint(self):
        blueprint = Blueprint("sitemap", self.__module__)
        blueprint.add_url_rule("/sitemap.xml", view_func=render_sitemap)
        blueprint.add_url_rule("/pure.xml", view_func=render_pure)
        #blueprint.add_url_rule("/commons.xsd", view_func=render_commons)
        #blueprint.add_url_rule("/dataset.xsd", view_func=render_dataset)

        # Use this to debug routes
        #blueprint.add_url_rule("/testme", view_func=testme)
        return blueprint
        
