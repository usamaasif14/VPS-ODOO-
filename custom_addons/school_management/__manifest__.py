{
    'name': 'School Management System',
    'version': '19.0.1.0.0',
    'summary': 'Complete School Management System with WhatsApp Integration',
    'description': """
        Complete School Management System for Odoo 19.
        Features:
        - Student Management (Admission, Profile, Roll Number)
        - Class & Section Management
        - Teacher Management & Schedule
        - Fee Structure & Student Ledger
        - Attendance Management
        - Exam & Result Management
        - WhatsApp Notifications
        - Class Schedule / Timetable
        - Homework Management
        - Library Management
        - Transport Management
    """,
    'category': 'Education',
    'author': 'MBO',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'hr',
        'product',
        'web',
    ],
    'data': [
        # Security
        'security/school_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/school_sequence_data.xml',
        'data/fee_type_data.xml',

        # Views
        'views/school_class_views.xml',
        'views/school_section_views.xml',
        'views/school_subject_views.xml',
        'views/school_teacher_views.xml',
        'views/school_student_views.xml',
        'views/school_fee_structure_views.xml',
        'views/school_fee_invoice_views.xml',
        'views/school_student_ledger_views.xml',
        'views/school_attendance_views.xml',
        'views/school_timetable_views.xml',
        'views/school_exam_views.xml',
        'views/school_result_views.xml',
        'views/school_homework_views.xml',
        'views/school_whatsapp_views.xml',
        'views/school_dashboard_views.xml',

        # Reports
        'reports/report_student_profile.xml',
        'reports/report_fee_invoice.xml',
        'reports/report_student_ledger.xml',
        'reports/report_timetable.xml',
        'reports/report_result_card.xml',
        'reports/report_fee_structure.xml',
        'reports/report_templates.xml',

        # Wizards
        'wizards/school_fee_wizard_views.xml',
        'wizards/school_result_wizard_views.xml',
        'wizards/school_whatsapp_wizard_views.xml',
        'wizards/school_attendance_wizard_views.xml',

        # Menus (must be last — references actions from views AND wizards)
        'views/school_menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'school_management/static/src/css/school_style.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
