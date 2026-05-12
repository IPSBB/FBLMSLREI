# -*- coding: utf-8 -*-
# Part of Creyox Technologies

{
    "name": 'Period Lock | Transaction Date Control | Accounting Lock Manager | Timed Journal Restriction | Accounting Period Shield | Journal Date Guard',
    "author": "Creyox Technologies",
    "website": "https://www.creyox.com",
    "support": "support@creyox.com",
    "category": 'Accounting',
    "description":
        """Period Lock restricts accounting transactions to a specific
           date range by locking journals. It prevents posting outside the set 
           period and allows authorized users to unlock when needed, ensuring
           control and accuracy in financial reporting.
        """,
    "license": 'LGPL-3',
    "version": '17.0.0.1',
    "price": 0,
    "currency": "USD",
    "summary": """
        Journal Date Guard is a powerful tool designed to control and restrict 
        accounting transactions within a specific date range. By locking journals
        such as vendor and customer bills, it prevents users from posting transactions 
        outside the designated period, ensuring better control over accounting periods. 
        Authorized users can unlock periods when necessary, offering flexibility while 
        maintaining security. This module is essential for ensuring accuracy and compliance 
        in financial reporting by preventing unauthorized or accidental posting beyond the 
        allowed timeframe.
        Period Lock,
        Transaction Date Control,
        Accounting Lock Manager,
        Timed Journal Restriction,
        Accounting Period Shield,
        Journal Date Guard,
    """,
    "depends": ["base", "account"],
    "data": [
         "security/period_lock_groups.xml",
        "security/ir.model.access.csv",
        "views/account_period_lock.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    "images": ["static/description/banner.png", ],
}
