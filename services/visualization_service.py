"""
Visualization Service for Query LangGraph (querylanggraph02).

Generates accurate, dynamic, and flexible Matplotlib charts (Line, Multi-Line, Bar)
from retrieved AIOps data (metrics, incidents, failure modes, severity, forecasts, reliability, feature importance)
and converts them to Base64-encoded PNG strings for embedding in JSON API chatbot responses.
"""

import io
import base64
import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — no GUI required
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

logger = logging.getLogger("QueryLangGraph.Services.VisualizationService")


class VisualizationService:
    """
    Enterprise Matplotlib visualization engine for AIOps queries.

    Supports dynamic chart generation for:
    - Metrics (CPU, Memory, Latency, Throughput over time or per service)
    - Failure Modes (Incident distribution, failure mode frequencies, confidence levels)
    - Severity (Severity escalation breakdown, incident severity counts)
    - Forecasts (Predicted metrics, time-to-failure trends)
    - Reliability (SLO compliance, error budget status)
    - Feature Contribution (Feature importance ranking bar charts)
    """

    CHART_COLOR_PALETTE = [
        "#4E9AF1", "#F16B4E", "#4EF19A", "#F1C44E",
        "#C44EF1", "#4EC4F1", "#F14E8A", "#A8F14E"
    ]

    FIGURE_SIZE = (10, 5)
    DPI = 120
    BACKGROUND_COLOR = "#0F1117"
    GRID_COLOR = "#2A2D3E"
    TEXT_COLOR = "#E0E0E0"
    AXIS_COLOR = "#3A3D4E"

    def generate(
        self,
        data: Dict[str, Any],
        chart_type: str,
        x_axis: str,
        y_axis: str,
        title: str,
        primary_category: str = "metrics"
    ) -> Dict[str, Any]:
        """
        Generate visualization from retrieved data and return Base64-encoded payload.

        Args:
            data (Dict[str, Any]): Retrieved data keyed by category.
            chart_type (str): 'line', 'multi_line', or 'bar'.
            x_axis (str): Column name to use on X axis.
            y_axis (str): Column name to use on Y axis.
            title (str): Chart title.
            primary_category (str): Primary query category to select rows for visualization.

        Returns:
            Dict[str, Any]: Payload containing base64_image, chart_type, title, metadata.
        """
        rows, category_key = self._extract_rows_and_category(data, primary_category)

        if not rows:
            logger.warning("VisualizationService: No data available to generate chart.")
            return {
                "base64_image": None,
                "chart_type": chart_type,
                "title": title,
                "error": "No data available for visualization."
            }

        # Specialized rendering for failure modes, feature contribution, severity if requested
        if category_key == "incident" or "failure_mode" in rows[0]:
            return self._generate_failure_mode_chart(rows, title)
        elif category_key == "feature_contribution" or "importance_score" in rows[0]:
            return self._generate_feature_contribution_chart(rows, title)

        # General dynamic column resolution
        x_col = self._resolve_column(rows, x_axis, fallback_options=["timestamp", "service", "id"])
        y_col = self._resolve_column(rows, y_axis, fallback_options=[
            "metric_value", "forecast_value", "slo_percentage", "confidence", "importance_score", "time_to_failure_mins"
        ])

        logger.info(f"VisualizationService: Generating '{chart_type}' chart | cat={category_key}, x={x_col}, y={y_col}, rows={len(rows)}")

        chart_lower = str(chart_type).lower()
        if chart_lower == "bar" or not self._is_numeric_column(rows, y_col):
            base64_img = self._generate_bar_chart(rows, x_col, y_col, title)
        elif chart_lower == "multi_line" and "service" in rows[0]:
            base64_img = self._generate_multi_line_chart(rows, x_col, y_col, title)
        else:
            base64_img = self._generate_line_chart(rows, x_col, y_col, title)

        return {
            "base64_image": base64_img,
            "chart_type": chart_lower,
            "title": title,
            "x_axis": x_col,
            "y_axis": y_col,
            "data_points": len(rows),
            "metadata": {
                "dpi": self.DPI,
                "format": "png",
                "encoding": "base64",
                "theme": "dark"
            }
        }

    def _extract_rows_and_category(
        self, data: Dict[str, Any], primary_category: str
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Extract the most relevant row list and category key from retrieved data."""
        if primary_category in data and isinstance(data[primary_category], list) and data[primary_category]:
            return data[primary_category], primary_category
        for key, val in data.items():
            if isinstance(val, list) and len(val) > 0:
                return val, key
        return [], primary_category

    def _resolve_column(
        self,
        rows: List[Dict[str, Any]],
        preferred: str,
        fallback_options: List[str]
    ) -> str:
        """Resolve actual column name in row schema."""
        sample = rows[0] if rows else {}
        if preferred in sample:
            return preferred
        for col in fallback_options:
            if col in sample:
                return col
        return list(sample.keys())[0] if sample else "value"

    def _is_numeric_column(self, rows: List[Dict[str, Any]], col: str) -> bool:
        """Check if column values are predominantly numeric."""
        if not rows:
            return False
        sample_vals = [r.get(col) for r in rows[:10] if r.get(col) is not None]
        numeric_count = 0
        for v in sample_vals:
            try:
                float(v)
                numeric_count += 1
            except (TypeError, ValueError):
                pass
        return numeric_count > len(sample_vals) / 2

    def _apply_dark_theme(self, fig: plt.Figure, ax: plt.Axes, title: str) -> None:
        """Apply dark AIOps aesthetic theme to figure."""
        fig.patch.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_facecolor(self.BACKGROUND_COLOR)
        ax.set_title(title, color=self.TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
        ax.tick_params(colors=self.TEXT_COLOR, labelsize=9)
        ax.xaxis.label.set_color(self.TEXT_COLOR)
        ax.yaxis.label.set_color(self.TEXT_COLOR)
        for spine in ax.spines.values():
            spine.set_edgecolor(self.AXIS_COLOR)
        ax.grid(True, color=self.GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.6)

    def _generate_failure_mode_chart(self, rows: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        """Generate specialized chart for failure modes and incident frequencies."""
        try:
            fm_counts = Counter([str(r.get("failure_mode", "unknown")) for r in rows])
            labels = list(fm_counts.keys())
            counts = list(fm_counts.values())

            fig, ax = plt.subplots(figsize=self.FIGURE_SIZE, dpi=self.DPI)
            bars = ax.barh(
                labels, counts,
                color=[self.CHART_COLOR_PALETTE[i % len(self.CHART_COLOR_PALETTE)] for i in range(len(labels))],
                edgecolor=self.AXIS_COLOR,
                height=0.55
            )
            for bar in bars:
                ax.text(
                    bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                    f"{int(bar.get_width())}",
                    va="center", ha="left", color=self.TEXT_COLOR, fontsize=9, fontweight="bold"
                )

            ax.set_xlabel("Incident Occurrence Count", fontsize=10)
            ax.set_ylabel("Failure Mode", fontsize=10)
            chart_title = title if "AIOps" not in title else "Failure Mode Frequency & Distribution"
            self._apply_dark_theme(fig, ax, chart_title)
            plt.tight_layout()
            base64_img = self._encode_to_base64(fig)
            plt.close("all")

            return {
                "base64_image": base64_img,
                "chart_type": "bar",
                "title": chart_title,
                "x_axis": "count",
                "y_axis": "failure_mode",
                "data_points": len(rows),
                "metadata": {"dpi": self.DPI, "format": "png", "encoding": "base64", "theme": "dark"}
            }
        except Exception as e:
            logger.error(f"VisualizationService._generate_failure_mode_chart: {e}")
            plt.close("all")
            return {"base64_image": None, "chart_type": "bar", "title": title, "error": str(e)}

    def _generate_feature_contribution_chart(self, rows: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        """Generate horizontal ranking bar chart for feature importance contribution."""
        try:
            sorted_rows = sorted(rows, key=lambda r: self._safe_float(r.get("importance_score", 0)), reverse=True)[:10]
            features = [str(r.get("feature_name", "unknown")) for r in sorted_rows][::-1]
            scores = [self._safe_float(r.get("importance_score", 0)) for r in sorted_rows][::-1]

            fig, ax = plt.subplots(figsize=self.FIGURE_SIZE, dpi=self.DPI)
            bars = ax.barh(features, scores, color=self.CHART_COLOR_PALETTE[0], edgecolor=self.AXIS_COLOR, height=0.55)
            for bar in bars:
                ax.text(
                    bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                    f"{bar.get_width():.3f}",
                    va="center", ha="left", color=self.TEXT_COLOR, fontsize=8
                )

            ax.set_xlabel("Importance Score", fontsize=10)
            ax.set_ylabel("Telemetry Feature", fontsize=10)
            chart_title = title if "AIOps" not in title else "Feature Importance & Root Cause Contribution"
            self._apply_dark_theme(fig, ax, chart_title)
            plt.tight_layout()
            base64_img = self._encode_to_base64(fig)
            plt.close("all")

            return {
                "base64_image": base64_img,
                "chart_type": "bar",
                "title": chart_title,
                "x_axis": "importance_score",
                "y_axis": "feature_name",
                "data_points": len(sorted_rows),
                "metadata": {"dpi": self.DPI, "format": "png", "encoding": "base64", "theme": "dark"}
            }
        except Exception as e:
            logger.error(f"VisualizationService._generate_feature_contribution_chart: {e}")
            plt.close("all")
            return {"base64_image": None, "chart_type": "bar", "title": title, "error": str(e)}

    def _generate_line_chart(
        self,
        rows: List[Dict[str, Any]],
        x_col: str,
        y_col: str,
        title: str
    ) -> Optional[str]:
        """Generate single-line time-series chart."""
        try:
            x_vals = [r.get(x_col, "") for r in rows]
            y_vals = self._safe_float_list([r.get(y_col, 0) for r in rows])
            x_parsed = self._try_parse_timestamps(x_vals)

            fig, ax = plt.subplots(figsize=self.FIGURE_SIZE, dpi=self.DPI)
            ax.plot(
                x_parsed, y_vals,
                color=self.CHART_COLOR_PALETTE[0],
                linewidth=2,
                marker="o",
                markersize=4,
                label=y_col
            )
            ax.fill_between(x_parsed, y_vals, alpha=0.15, color=self.CHART_COLOR_PALETTE[0])
            ax.set_xlabel(x_col, fontsize=10)
            ax.set_ylabel(y_col, fontsize=10)

            if x_parsed and isinstance(x_parsed[0], datetime):
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
                fig.autofmt_xdate(rotation=30)

            ax.legend(facecolor=self.BACKGROUND_COLOR, labelcolor=self.TEXT_COLOR, fontsize=9)
            self._apply_dark_theme(fig, ax, title)
            plt.tight_layout()
            return self._encode_to_base64(fig)
        except Exception as e:
            logger.error(f"VisualizationService._generate_line_chart: {e}")
            return None
        finally:
            plt.close("all")

    def _generate_multi_line_chart(
        self,
        rows: List[Dict[str, Any]],
        x_col: str,
        y_col: str,
        title: str
    ) -> Optional[str]:
        """Generate multi-line time-series chart grouped by service."""
        try:
            services = sorted(set(str(r.get("service", "unknown")) for r in rows))
            fig, ax = plt.subplots(figsize=self.FIGURE_SIZE, dpi=self.DPI)

            for idx, service in enumerate(services):
                svc_rows = [r for r in rows if str(r.get("service", "")) == service]
                x_vals = [r.get(x_col, "") for r in svc_rows]
                y_vals = self._safe_float_list([r.get(y_col, 0) for r in svc_rows])
                x_parsed = self._try_parse_timestamps(x_vals)

                color = self.CHART_COLOR_PALETTE[idx % len(self.CHART_COLOR_PALETTE)]
                ax.plot(x_parsed, y_vals, label=service, color=color, linewidth=2, marker="o", markersize=3)

            ax.set_xlabel(x_col, fontsize=10)
            ax.set_ylabel(y_col, fontsize=10)
            ax.legend(facecolor=self.BACKGROUND_COLOR, labelcolor=self.TEXT_COLOR, fontsize=9, loc="upper right")
            self._apply_dark_theme(fig, ax, title)

            if rows and isinstance(self._try_parse_timestamps([rows[0].get(x_col, "")])[0], datetime):
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
                fig.autofmt_xdate(rotation=30)

            plt.tight_layout()
            return self._encode_to_base64(fig)
        except Exception as e:
            logger.error(f"VisualizationService._generate_multi_line_chart: {e}")
            return None
        finally:
            plt.close("all")

    def _generate_bar_chart(
        self,
        rows: List[Dict[str, Any]],
        x_col: str,
        y_col: str,
        title: str
    ) -> Optional[str]:
        """Generate categorical bar chart."""
        try:
            category_col = "service" if "service" in (rows[0] if rows else {}) else x_col
            agg: Dict[str, List[float]] = {}
            for r in rows:
                cat = str(r.get(category_col, "unknown"))
                val = self._safe_float(r.get(y_col, 0))
                agg.setdefault(cat, []).append(val)

            labels = list(agg.keys())
            values = [sum(v) / len(v) for v in agg.values()]

            fig, ax = plt.subplots(figsize=self.FIGURE_SIZE, dpi=self.DPI)
            bars = ax.barh(
                labels, values,
                color=[self.CHART_COLOR_PALETTE[i % len(self.CHART_COLOR_PALETTE)] for i in range(len(labels))],
                edgecolor=self.AXIS_COLOR, height=0.55
            )
            for bar in bars:
                ax.text(
                    bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{bar.get_width():.2f}",
                    va="center", ha="left", color=self.TEXT_COLOR, fontsize=8
                )

            ax.set_xlabel(f"Avg {y_col}", fontsize=10)
            ax.set_ylabel(category_col, fontsize=10)
            self._apply_dark_theme(fig, ax, title)
            plt.tight_layout()
            return self._encode_to_base64(fig)
        except Exception as e:
            logger.error(f"VisualizationService._generate_bar_chart: {e}")
            return None
        finally:
            plt.close("all")

    def _encode_to_base64(self, fig: plt.Figure) -> Optional[str]:
        """Render Matplotlib figure to in-memory Base64 buffer."""
        try:
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
            buf.seek(0)
            encoded = base64.b64encode(buf.read()).decode("utf-8")
            buf.close()
            return encoded
        except Exception as e:
            logger.error(f"VisualizationService._encode_to_base64: {e}")
            return None

    def _try_parse_timestamps(self, values: List[Any]) -> List[Any]:
        """Parse timestamp strings into datetime objects."""
        FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
        parsed = []
        for v in values:
            converted = None
            for fmt in FORMATS:
                try:
                    converted = datetime.strptime(str(v), fmt)
                    break
                except (ValueError, TypeError):
                    continue
            parsed.append(converted if converted else v)
        return parsed

    def _safe_float(self, val: Any) -> float:
        """Safely convert value to float."""
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    def _safe_float_list(self, values: List[Any]) -> List[float]:
        """Safely convert list to floats."""
        return [self._safe_float(v) for v in values]


# Type hint helper
Tuple_Row_Category = Tuple[List[Dict[str, Any]], str]
