/**
 * Dashboard Chart Initialization
 * Parses dynamic JSON script data and builds the ApexCharts report chart.
 */
document.addEventListener("DOMContentLoaded", () => {
  const chartSalesEl = document.getElementById('chart-sales-data');
  const chartRevenueEl = document.getElementById('chart-revenue-data');
  const chartDatesEl = document.getElementById('chart-dates-data');
  
  if (chartSalesEl && chartRevenueEl && chartDatesEl) {
    const chartSales = JSON.parse(chartSalesEl.textContent);
    const chartRevenue = JSON.parse(chartRevenueEl.textContent);
    const chartDates = JSON.parse(chartDatesEl.textContent);

    new ApexCharts(document.querySelector("#reportsChart"), {
      series: [{
        name: 'Sales Count',
        data: chartSales
      }, {
        name: 'Revenue ($)',
        data: chartRevenue
      }],
      chart: {
        height: 350,
        type: 'area',
        toolbar: {
          show: false
        },
      },
      markers: {
        size: 4
      },
      colors: ['#4154f1', '#2eca6a'],
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 1,
          opacityFrom: 0.3,
          opacityTo: 0.4,
          stops: [0, 90, 100]
        }
      },
      dataLabels: {
        enabled: false
      },
      stroke: {
        curve: 'smooth',
        width: 2
      },
      xaxis: {
        type: 'category',
        categories: chartDates
      },
      tooltip: {
        x: {
          format: 'yyyy-MM-dd'
        },
        y: {
          formatter: function (value, { seriesIndex }) {
            if (seriesIndex === 0) {
              return value.toLocaleString();
            }
            return '$' + value.toLocaleString();
          }
        }
      },
      yaxis: {
        labels: {
          formatter: function (value) {
            return value.toLocaleString();
          }
        }
      }
    }).render();
  }
});
