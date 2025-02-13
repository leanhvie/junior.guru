from datetime import date

import pytest

from juniorguru.cli.students import subscription_to_row, to_csv
from juniorguru.models.company import Company, CompanyStudentSubscription


def test_to_csv():
    rows = [{'a': 1, 'b': 2, 'c': 3},
            {'a': None, 'b': 2, 'c': 3},
            {'a': 1, 'b': None, 'c': 3}]
    assert to_csv(rows) == (
        'a,b,c\r\n'
        '1,2,3\r\n'
        ',2,3\r\n'
        '1,,3\r\n'
    )


def test_to_csv_empty():
    rows = []
    with pytest.raises(ValueError):
        assert to_csv(rows)


def test_subscription_to_row():
    company = Company(name='Foo Corporation',
                      logo_filename='foo.svg',
                      url='https://example.com',
                      starts_on=date.today())
    subscription = CompanyStudentSubscription(id='123',
                                              company=company,
                                              account_id='12345',
                                              name='Honza',
                                              email='honza@example.com',
                                              started_on=date.today(),
                                              invoiced_on=date.today())

    assert subscription_to_row(subscription) == dict(name='Honza',
                                                     email='honza@example.com',
                                                     started_on=date.today(),
                                                     invoiced_on=date.today())
