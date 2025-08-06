/**
 * Metrics Chart component
 * Displays real-time queue metrics using Chart.js
 */

import React, { useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const MetricsChart = ({ queues }) => {
  const chartRef = useRef();

  // Generate mock historical data for demonstration
  const generateMockData = () => {
    const now = new Date();
    const labels = [];
    const datasets = [];

    // Generate time labels for last hour (every 5 minutes)
    for (let i = 11; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 5 * 60 * 1000);
      labels.push(time.toLocaleTimeString('sv-SE', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }));
    }

    // Create dataset for each queue
    const colors = [
      { border: '#007bff', background: 'rgba(0, 123, 255, 0.1)' },
      { border: '#28a745', background: 'rgba(40, 167, 69, 0.1)' },
      { border: '#ffc107', background: 'rgba(255, 193, 7, 0.1)' },
      { border: '#dc3545', background: 'rgba(220, 53, 69, 0.1)' }
    ];

    queues.forEach((queue, index) => {
      const color = colors[index % colors.length];
      const data = [];
      
      // Generate mock historical data points
      for (let i = 0; i < 12; i++) {
        const baseWaitTime = queue.current_wait_time || 10;
        const variation = Math.random() * 10 - 5; // ±5 seconds variation
        const waitTime = Math.max(0, baseWaitTime + variation);
        data.push(Math.round(waitTime));
      }

      datasets.push({
        label: queue.queue_name,
        data: data,
        borderColor: color.border,
        backgroundColor: color.background,
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: color.border,
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      });
    });

    return { labels, datasets };
  };

  const chartData = generateMockData();

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12
          }
        }
      },
      title: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#ddd',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y}s`;
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Tid',
          font: {
            size: 12,
            weight: 'bold'
          }
        },
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Väntetid (sekunder)',
          font: {
            size: 12,
            weight: 'bold'
          }
        },
        min: 0,
        max: 30,
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          callback: function(value) {
            return value + 's';
          }
        }
      }
    },
    elements: {
      line: {
        tension: 0.4
      }
    }
  };

  // Add reference lines for warning and critical thresholds
  const plugins = [{
    id: 'thresholdLines',
    beforeDraw: (chart) => {
      const { ctx, chartArea: { left, right, top, bottom }, scales: { y } } = chart;
      
      // Warning line at 15 seconds
      const warningY = y.getPixelForValue(15);
      ctx.save();
      ctx.strokeStyle = '#ffc107';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(left, warningY);
      ctx.lineTo(right, warningY);
      ctx.stroke();
      
      // Critical line at 20 seconds
      const criticalY = y.getPixelForValue(20);
      ctx.strokeStyle = '#dc3545';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(left, criticalY);
      ctx.lineTo(right, criticalY);
      ctx.stroke();
      ctx.restore();
    }
  }];

  if (!queues || queues.length === 0) {
    return (
      <div className="text-center py-5">
        <i className="fas fa-chart-line fa-3x text-muted mb-3"></i>
        <p className="text-muted">Ingen data att visa i diagrammet</p>
      </div>
    );
  }

  return (
    <div style={{ height: '300px', position: 'relative' }}>
      <Line 
        ref={chartRef}
        data={chartData} 
        options={options} 
        plugins={plugins}
      />
      <div className="mt-2">
        <small className="text-muted">
          <span className="me-3">
            <span style={{ color: '#ffc107' }}>━━━</span> Varningsgräns (15s)
          </span>
          <span>
            <span style={{ color: '#dc3545' }}>━━━</span> Kritisk gräns (20s)
          </span>
        </small>
      </div>
    </div>
  );
};

export default MetricsChart;
