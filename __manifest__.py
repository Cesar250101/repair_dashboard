{
    'name': 'Tablero de Reparaciones',
    'version': '16.0.1.2.0',
    'category': 'Inventory/Repair',
    'summary': 'Dashboard analítico para órdenes de reparación (repair.order)',
    'description': """
Tablero de Reparaciones
=======================
Agrega un menú *Dashboard* como primer elemento del módulo Reparaciones y lo
muestra por defecto al ingresar al módulo. Presenta KPIs y gráficos de las
órdenes de reparación con la paleta corporativa de Method.
""",
    'author': 'Method',
    'website': 'https://method.cl',
    'depends': ['repair', 'web'],
    'data': [
        'views/repair_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'repair_dashboard/static/src/scss/repair_dashboard.scss',
            'repair_dashboard/static/src/js/repair_dashboard.js',
            'repair_dashboard/static/src/xml/repair_dashboard.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
