import hashlib
import os
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urljoin

import arrow

from juniorguru.lib import charts
from juniorguru.mkdocs.thumbnail import thumbnail
from juniorguru.models.base import db
from juniorguru.models.club import ClubMessage, ClubSubscribedPeriod, ClubUser
from juniorguru.models.company import Company
from juniorguru.models.event import Event
from juniorguru.models.job import ListedJob
from juniorguru.models.podcast import PodcastEpisode
from juniorguru.models.story import Story
from juniorguru.models.topic import Topic
from juniorguru.models.transaction import Transaction


NOW = arrow.utcnow()

TODAY = NOW.date()

PREVIOUS_MONTH = TODAY.replace(day=1) - timedelta(days=1)

BUSINESS_BEGIN_ON = date(2020, 1, 1)

CLUB_BEGIN_ON = date(2021, 2, 1)

CLOUDINARY_HOST = os.getenv('CLOUDINARY_HOST', 'res.cloudinary.com')


####################################################################
# SHARED DOCS AND THEME CONTEXT                                    #
####################################################################


@db.connection_context()
def on_shared_context(context):
    context['now'] = NOW
    context['today'] = TODAY
    context['profit_ttm'] = Transaction.profit_ttm(TODAY)
    context['revenue_ttm_breakdown'] = Transaction.revenue_ttm_breakdown(TODAY)
    context['cloudinary_host'] = CLOUDINARY_HOST


def on_shared_page_context(context, page, config, files):
    pass


####################################################################
# DOCS CONTEXT                                                     #
####################################################################


@db.connection_context()
def on_docs_context(context):
    # topics/*
    context['club_elapsed_months'] = int(round((TODAY - CLUB_BEGIN_ON).days / 30))
    context['members'] = ClubUser.avatars_listing()
    context['members_total_count'] = ClubUser.members_count()

    # club.md
    context['finaid_url'] = 'https://docs.google.com/forms/d/e/1FAIpQLSeJ_Bmq__X8AA-XbKqU-Vr1N6fdGHSBQ-IuneO5zhBcGCOgjQ/viewform?usp=sf_link'
    context['messages_count'] = ClubMessage.count()
    context['companies'] = Company.listing()
    context['companies_schools'] = Company.schools_listing()
    context['events'] = Event.listing()

    # handbook/motivation.md
    context['stories'] = Story.listing()
    context['stories_by_tags'] = Story.tags_mapping()

    # handbook/candidate.md
    context['jobs'] = ListedJob.listing()
    context['jobs_remote'] = ListedJob.remote_listing()
    context['jobs_internship'] = ListedJob.internship_listing()
    context['jobs_volunteering'] = ListedJob.volunteering_listing()

    # open.md
    business_charts_months = charts.months(BUSINESS_BEGIN_ON, TODAY)
    context['charts_business_labels'] = charts.labels(business_charts_months)
    context['charts_profit'] = charts.per_month(Transaction.profit, business_charts_months)
    context['charts_profit_ttm'] = charts.per_month(Transaction.profit_ttm, business_charts_months)
    context['charts_revenue'] = charts.per_month(Transaction.revenue, business_charts_months)
    context['charts_revenue_ttm'] = charts.per_month(Transaction.revenue_ttm, business_charts_months)
    context['charts_revenue_breakdown'] = charts.per_month_breakdown(Transaction.revenue_breakdown, business_charts_months)
    context['charts_cost'] = charts.per_month(Transaction.cost, business_charts_months)
    context['charts_cost_ttm'] = charts.per_month(Transaction.cost_ttm, business_charts_months)
    context['charts_cost_breakdown'] = charts.per_month_breakdown(Transaction.cost_breakdown, business_charts_months)
    club_charts_months = charts.months(CLUB_BEGIN_ON, TODAY)
    context['charts_club_labels'] = charts.labels(club_charts_months)
    context['charts_subscriptions'] = charts.per_month(ClubSubscribedPeriod.count, club_charts_months)
    context['charts_individuals'] = charts.per_month(ClubSubscribedPeriod.individuals_count, club_charts_months)
    context['charts_women'] = charts.per_month(ClubSubscribedPeriod.women_count, club_charts_months)
    context['charts_subscriptions_breakdown'] = charts.per_month_breakdown(ClubSubscribedPeriod.count_breakdown, club_charts_months)
    context['charts_women_ptc'] = charts.per_month(ClubSubscribedPeriod.women_ptc, club_charts_months)
    context['charts_individuals_duration'] = charts.per_month(ClubSubscribedPeriod.individuals_duration_avg, club_charts_months)
    club_trend_charts_months = charts.months(CLUB_BEGIN_ON, PREVIOUS_MONTH)
    context['charts_club_trend_labels'] = charts.labels(club_trend_charts_months)
    context['charts_signups'] = charts.per_month(ClubSubscribedPeriod.signups_count, club_trend_charts_months)
    context['charts_individuals_signups'] = charts.per_month(ClubSubscribedPeriod.individuals_signups_count, club_trend_charts_months)
    context['charts_churn_ptc'] = charts.per_month(ClubSubscribedPeriod.churn_ptc, club_trend_charts_months)
    context['charts_individuals_churn_ptc'] = charts.per_month(ClubSubscribedPeriod.individuals_churn_ptc, club_trend_charts_months)

    # podcast.md, handbook/cv.md
    context['podcast_episodes'] = PodcastEpisode.listing()


@db.connection_context()
def on_docs_page_context(context, page, config, files):
    if 'topic_name' in page.meta:
        topic_name = page.meta['topic_name']
        context['topic'] = Topic.get_by_id(topic_name)


####################################################################
# THEME CONTEXT                                                    #
####################################################################


def on_theme_context(context):
    js_path = Path(__file__).parent.parent / 'web' / 'static' / 'bundle.js'
    css_path = Path(__file__).parent.parent / 'web' / 'static' / 'bundle-mkdocs.css'
    context['js_hash'] = hash_file(js_path)
    context['css_hash'] = hash_file(css_path)
    context['bootstrap_icons_file'] = re.search(r'bootstrap-icons.woff2\?\w+', css_path.read_text()).group(0)

    context['companies_handbook'] = Company.handbook_listing()


@db.connection_context()
def on_theme_page_context(context, page, config, files):
    page.meta.setdefault('title', 'Jak se naučit programovat a získat první práci v IT')

    thumbnail_path = thumbnail(page.meta.get('thumbnail_title', page.meta['title']),
                               badge=page.meta.get('thumbnail_badge'))
    context['thumbnail_url'] = urljoin(config['site_url'], f'static/{thumbnail_path}')

    context['parent_page'] = get_parent_page(page)
    context['previous_page'] = get_sibling_page(page, -1)
    context['next_page'] = get_sibling_page(page, +1)


####################################################################
# HELPER FUNCTIONS                                                 #
####################################################################


def hash_file(path):
    hash = hashlib.sha512()
    hash.update(path.read_bytes())
    return hash.hexdigest()


def get_parent_page(page):
    try:
        return page.parent.children[0]
    except AttributeError:
        return None


def get_sibling_page(page, offset):
    try:
        index = page.parent.children.index(page)
        sibling_index = max(index + offset, 0)
        if index == sibling_index:
            return None
        return page.parent.children[sibling_index]
    except (AttributeError, IndexError):
        return None
