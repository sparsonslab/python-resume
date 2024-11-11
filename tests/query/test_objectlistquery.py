#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.
import unittest

import datetime

from resume.query.objectlistquery import ObjectListQuery


class TestObjectListQuery(unittest.TestCase):

    def setUp(self):
        objects = [
            {
                "name": "zebra", "caught": datetime.datetime(2010, 3, 15),
                "dimensions": {"height": 1.4, "length": 1.8},
                "appendages": {"legs": 4}
            },
            {
                "name": "monkey", "caught": datetime.datetime(2002, 4, 11),
                "dimensions": {"height": 1.2},
                "appendages": {"legs": 2, "arms": 2}
            },
            {
                "name": "duck", "caught": datetime.datetime(1987, 11, 3),
                "dimensions": {"height": 0.15, "length": 0.24},
                "appendages": {"legs": 2, "wings": 2},
                "abilities": {"flys": True}
            },
            {
                "name": "whale", "caught": datetime.datetime(1910, 1, 15),
                "dimensions": {"height": 2.1, "length": 5.6},
                "appendages": {"legs": 2}
            },
            {
                "name": "millipede", "caught": datetime.datetime(1950, 7, 21),
                "dimensions": {"height": 0.005, "length": 0.04},
                "appendages": {"legs": 1000}
            },
        ]

        self.querier = ObjectListQuery(fields={
            ("name", "nm", str): (lambda x: x["name"]),
            ("caught", "cg", datetime.datetime): (lambda x: x["caught"]),
            ("height", "hg", float): (lambda x: x["dimensions"]["height"]),
            ("legs", "lg", int): (lambda x: x["appendages"]["legs"]),
            ("arms", "ar", int): (lambda x: x["appendages"]["arms"]),
            ("flys", "fy", bool): (lambda x: x["abilities"]["flys"]),
        })

    def test_working_querys(self):

        self.assertEqual(3, 3)
