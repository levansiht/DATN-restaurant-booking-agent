import { useEffect, useRef } from "react";
import ApexCharts from "apexcharts";

const CURRENCY_FORMATTER = new Intl.NumberFormat("vi-VN", {
  style: "currency",
  currency: "VND",
  maximumFractionDigits: 0,
});

const COMPACT_FORMATTER = new Intl.NumberFormat("vi-VN", {
  notation: "compact",
  maximumFractionDigits: 1,
});

function buildOptions(series, categories) {
  return {
    chart: {
      type: "area",
      height: 320,
      fontFamily: "inherit",
      toolbar: { show: false },
      zoom: { enabled: false },
      animations: { easing: "easeinout", speed: 400 },
    },
    colors: ["#16a34a", "#d97706"],
    dataLabels: { enabled: false },
    stroke: { curve: "smooth", width: 2 },
    fill: {
      type: "gradient",
      gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.05, stops: [0, 90, 100] },
    },
    grid: { borderColor: "#e7e5e4", strokeDashArray: 4 },
    legend: { position: "top", horizontalAlign: "right", markers: { radius: 12 } },
    series,
    xaxis: {
      categories,
      tickAmount: Math.min(categories.length, 8),
      labels: { rotate: 0, style: { colors: "#78716c", fontSize: "11px" } },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      labels: {
        style: { colors: "#78716c", fontSize: "11px" },
        formatter: (value) => COMPACT_FORMATTER.format(value || 0),
      },
    },
    tooltip: {
      y: { formatter: (value) => CURRENCY_FORMATTER.format(value || 0) },
    },
  };
}

export default function RevenueChart({ series, categories }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) {
      return undefined;
    }
    const chart = new ApexCharts(containerRef.current, buildOptions(series, categories));
    chart.render();
    chartRef.current = chart;
    return () => {
      chart.destroy();
      chartRef.current = null;
    };
    // Build once; subsequent updates handled by the effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!chartRef.current) {
      return;
    }
    chartRef.current.updateOptions(
      { xaxis: { categories } },
      false,
      false,
    );
    chartRef.current.updateSeries(series, true);
  }, [series, categories]);

  return <div ref={containerRef} />;
}
