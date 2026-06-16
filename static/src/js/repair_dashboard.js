/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useRef, useState } from "@odoo/owl";

// Periodos de fecha disponibles en el filtro del encabezado
const PERIODS = [
    { value: "today", label: "Hoy" },
    { value: "yesterday", label: "Ayer" },
    { value: "this_week", label: "Esta semana" },
    { value: "this_month", label: "Este mes" },
    { value: "last_month", label: "Mes anterior" },
    { value: "same_month_last_year", label: "Mismo mes año anterior" },
    { value: "this_year", label: "Este año" },
    { value: "last_year", label: "Año anterior" },
    { value: "all", label: "Todo" },
];

// Paleta corporativa Method (tomada del logo)
const COLORS = {
    orange: "#F5841F",
    orangeLight: "#FBB040",
    slate: "#455160",
    slateLight: "#6B7787",
    slateDark: "#2F3845",
};

// Color por estado de la orden de reparación
const STATE_COLORS = {
    draft: "#94A3B8",
    confirmed: COLORS.slate,
    ready: COLORS.orangeLight,
    under_repair: COLORS.orange,
    "2binvoiced": "#D97706",
    done: "#16A34A",
    cancel: "#DC2626",
};

export class RepairDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.periods = PERIODS;
        this.state = useState({ data: null, loading: true, period: "this_month" });
        this.stateChartRef = useRef("stateChart");
        this.trendChartRef = useRef("trendChart");
        this._charts = [];
        this._needRender = false;

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this._loadData();
        });
        onMounted(() => this._renderCharts());
        onPatched(() => {
            // Re-dibuja los gráficos cuando el canvas vuelve al DOM tras recargar
            if (this._needRender && !this.state.loading && this.stateChartRef.el) {
                this._needRender = false;
                this._renderCharts();
            }
        });
        onWillUnmount(() => this._destroyCharts());
    }

    async _loadData() {
        this.state.loading = true;
        this.state.data = await this.orm.call("repair.order", "get_dashboard_data", [
            this.state.period,
        ]);
        this.state.loading = false;
    }

    async reload() {
        this._needRender = true;
        await this._loadData();
    }

    onPeriodChange(ev) {
        this.state.period = ev.target.value;
        this.reload();
    }

    get kpis() {
        return (this.state.data && this.state.data.kpis) || {};
    }

    formatAmount(value) {
        const cur = (this.state.data && this.state.data.currency) || { symbol: "$", position: "before" };
        const num = (value || 0).toLocaleString("es-CL", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });
        return cur.position === "after" ? `${num} ${cur.symbol}` : `${cur.symbol} ${num}`;
    }

    _destroyCharts() {
        this._charts.forEach((c) => c.destroy());
        this._charts = [];
    }

    _renderCharts() {
        if (!this.state.data || typeof Chart === "undefined") {
            return;
        }
        this._destroyCharts();
        const data = this.state.data;

        // --- Gráfico de dona: distribución por estado ---
        const byState = data.by_state.filter((s) => s.value > 0);
        if (this.stateChartRef.el && byState.length) {
            this._charts.push(
                new Chart(this.stateChartRef.el.getContext("2d"), {
                    type: "doughnut",
                    data: {
                        labels: byState.map((s) => s.label),
                        datasets: [
                            {
                                data: byState.map((s) => s.value),
                                backgroundColor: byState.map((s) => STATE_COLORS[s.key] || COLORS.slate),
                                borderWidth: 2,
                                borderColor: "#FFFFFF",
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: "62%",
                        plugins: {
                            legend: { position: "right", labels: { padding: 16, font: { size: 12 } } },
                        },
                    },
                })
            );
        }

        // --- Gráfico de barras: tendencia mensual ---
        if (this.trendChartRef.el) {
            this._charts.push(
                new Chart(this.trendChartRef.el.getContext("2d"), {
                    type: "bar",
                    data: {
                        labels: data.trend.labels,
                        datasets: [
                            {
                                label: "Órdenes creadas",
                                data: data.trend.values,
                                backgroundColor: COLORS.orange,
                                hoverBackgroundColor: COLORS.orangeLight,
                                borderRadius: 6,
                                maxBarThickness: 38,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#EEF2F6" } },
                            x: { grid: { display: false } },
                        },
                    },
                })
            );
        }
    }

    // Abre la lista de órdenes filtrada por estado (+ periodo) al hacer clic en una KPI
    openOrders(domain, title) {
        const dateDomain = (this.state.data && this.state.data.active_domain) || [];
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "repair.order",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: [...dateDomain, ...(domain || [])],
            target: "current",
        });
    }
}

RepairDashboard.template = "repair_dashboard.Dashboard";

registry.category("actions").add("repair_dashboard", RepairDashboard);
