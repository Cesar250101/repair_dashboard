from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    @api.model
    def _dashboard_period_range(self, period):
        """Devuelve (date_from, date_to) como objetos date para el periodo dado.

        date_to es exclusivo (límite superior). Si no hay rango, devuelve None.
        """
        today = fields.Date.context_today(self)
        if period == "today":
            return today, today + relativedelta(days=1)
        if period == "yesterday":
            return today - relativedelta(days=1), today
        if period == "this_week":
            start = today - relativedelta(days=today.weekday())
            return start, start + relativedelta(weeks=1)
        if period == "this_month":
            start = today.replace(day=1)
            return start, start + relativedelta(months=1)
        if period == "last_month":
            start = today.replace(day=1) - relativedelta(months=1)
            return start, start + relativedelta(months=1)
        if period == "same_month_last_year":
            start = today.replace(day=1) - relativedelta(years=1)
            return start, start + relativedelta(months=1)
        if period == "this_year":
            start = today.replace(month=1, day=1)
            return start, start + relativedelta(years=1)
        if period == "last_year":
            start = today.replace(month=1, day=1) - relativedelta(years=1)
            return start, start + relativedelta(years=1)
        # "all" u otro -> sin filtro
        return None

    @api.model
    def get_dashboard_data(self, period="this_month"):
        """Devuelve KPIs y series de datos para el tablero de reparaciones."""
        state_labels = dict(self._fields["state"].selection)

        # --- Dominio según el periodo seleccionado -----------------------------
        rng = self._dashboard_period_range(period)
        domain = []
        active_domain = []
        if rng:
            date_from, date_to = rng
            start_dt = fields.Datetime.to_string(datetime.combine(date_from, time.min))
            end_dt = fields.Datetime.to_string(datetime.combine(date_to, time.min))
            domain = [("create_date", ">=", start_dt), ("create_date", "<", end_dt)]
            active_domain = list(domain)

        # --- Conteo por estado -------------------------------------------------
        grouped = self.read_group(domain, ["state"], ["state"])
        counts = {key: 0 for key in state_labels}
        for line in grouped:
            if line.get("state"):
                counts[line["state"]] = line["state_count"]

        total_orders = sum(counts.values())

        # --- Montos ------------------------------------------------------------
        amount_groups = self.read_group(domain, ["amount_total:sum"], [])
        total_amount = amount_groups[0]["amount_total"] if amount_groups else 0.0

        open_states = ["confirmed", "ready", "under_repair"]
        open_groups = self.read_group(
            domain + [("state", "in", open_states)], ["amount_total:sum"], []
        )
        open_amount = open_groups[0]["amount_total"] if open_groups else 0.0

        currency = self.env.company.currency_id

        # --- Distribución por estado (para gráfico) ----------------------------
        by_state = [
            {"key": key, "label": label, "value": counts[key]}
            for key, label in state_labels.items()
        ]

        # --- Productos más reparados (campo product_id) ------------------------
        product_groups = self.read_group(
            domain + [("product_id", "!=", False)],
            ["product_id"],
            ["product_id"],
        )
        by_product = sorted(
            [
                {
                    "id": g["product_id"][0],
                    "name": g["product_id"][1],
                    "count": g["product_id_count"],
                }
                for g in product_groups
                if g.get("product_id")
            ],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        # --- Tendencia mensual (últimos 12 meses) ------------------------------
        today = fields.Date.context_today(self)
        first_of_month = today.replace(day=1)
        months, monthly_counts = [], []
        for i in range(11, -1, -1):
            month_start = first_of_month - relativedelta(months=i)
            month_end = month_start + relativedelta(months=1)
            start_dt = datetime.combine(month_start, time.min)
            end_dt = datetime.combine(month_end, time.min)
            count = self.search_count(
                [("create_date", ">=", start_dt), ("create_date", "<", end_dt)]
            )
            months.append(month_start.strftime("%m/%Y"))
            monthly_counts.append(count)

        return {
            "kpis": {
                "total_orders": total_orders,
                "draft": counts.get("draft", 0),
                "confirmed": counts.get("confirmed", 0),
                "under_repair": counts.get("under_repair", 0),
                "to_invoice": counts.get("2binvoiced", 0),
                "done": counts.get("done", 0),
                "cancel": counts.get("cancel", 0),
                "total_amount": total_amount,
                "open_amount": open_amount,
            },
            "by_state": by_state,
            "by_product": by_product,
            "trend": {"labels": months, "values": monthly_counts},
            "currency": {"symbol": currency.symbol, "position": currency.position},
            "period": period,
            "active_domain": active_domain,
        }
