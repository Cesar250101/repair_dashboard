"""Datos de actualización para la versión 16.0.1.5.0."""


def migrate(cr, version):
    """Completa la fecha RMA de órdenes creadas antes de este cambio."""
    cr.execute(
        """
        UPDATE repair_order
           SET fecha_rma = create_date::date
         WHERE fecha_rma IS NULL
           AND create_date IS NOT NULL
        """
    )
