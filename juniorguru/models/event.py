from datetime import datetime, timedelta

import arrow
from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, TextField

from juniorguru.lib.md import strip_links
from juniorguru.models.base import BaseModel, JSONField
from juniorguru.models.club import ClubUser


class Event(BaseModel):
    title = CharField()
    start_at = DateTimeField(index=True)
    description = TextField()
    poster_description = TextField(null=True)
    bio = TextField()
    avatar_path = CharField(null=True)
    bio_name = TextField()
    bio_title = TextField(null=True)
    bio_links = JSONField(default=lambda: [])
    recording_url = CharField(null=True)
    public_recording_url = CharField(null=True)
    poster_path = CharField(null=True)
    poster_ig_path = CharField(null=True)
    poster_yt_path = CharField(null=True)
    poster_dc_path = CharField(null=True)
    logo_path = CharField(null=True)
    discord_id = IntegerField(index=True, null=True)
    discord_url = CharField(null=True)

    @property
    def start_at_prg(self):
        return arrow.get(self.start_at).to('Europe/Prague').naive

    @property
    def end_at(self):
        return self.start_at + timedelta(hours=1)

    @property
    def description_plain(self):
        return strip_links(self.description.strip())

    @property
    def bio_plain(self):
        return strip_links(self.bio).strip()

    @property
    def slug(self):
        return self.start_at_prg.isoformat().replace(':', '-')

    @property
    def url(self):
        return f"https://junior.guru/events/#{self.slug}"

    @classmethod
    def next(cls, now=None):
        now = now or datetime.utcnow()
        return cls.select() \
            .where(cls.start_at >= now) \
            .order_by(cls.start_at) \
            .first()

    @classmethod
    def list_speaking_members(cls):
        return ClubUser.select() \
            .where(ClubUser.is_member == True) \
            .join(EventSpeaking)

    @classmethod
    def listing(cls):
        return cls.select() \
            .order_by(cls.start_at.desc())

    @classmethod
    def api_listing(cls):
        return cls.listing()

    @classmethod
    def archive_listing(cls, now=None):
        now = now or datetime.utcnow()
        return cls.select() \
            .where(cls.start_at < now) \
            .order_by(cls.start_at.desc())

    @classmethod
    def planned_listing(cls, now=None):
        now = now or datetime.utcnow()
        return cls.select() \
            .where(cls.start_at >= now) \
            .order_by(cls.start_at)


class EventSpeaking(BaseModel):
    speaker = ForeignKeyField(ClubUser, backref='list_speaking')
    event = ForeignKeyField(Event, backref='list_speaking')
