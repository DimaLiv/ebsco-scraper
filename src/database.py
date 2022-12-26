import os
import datetime
import logging

from peewee import *

logger = logging.getLogger()

db = SqliteDatabase(os.path.join('out', 'database.sqlite'))


def save_article(ext_id, url, title, source, database, text, report, publication_date):
    try:
        article = Article(
            ext_id=int(ext_id),
            url=url,
            title=title,
            source=source,
            database=database,
            text=text,
            report=report,
            publication_date=publication_date,
        )
        article.save()
    except Exception as e:
        logger.error("On url '{}' exception: {}".format(url, e))


class BaseModel(Model):
    class Meta:
        database = db


class Article(BaseModel):
    ext_id = IntegerField()
    url = TextField()
    title = TextField()
    source = TextField()
    database = TextField()
    report = TextField()
    text = TextField()
    publication_date = DateTimeField(null=True)
    created_date = DateTimeField(default=datetime.datetime.now)


def create_tables():
    with db:
        db.create_tables([Article])
