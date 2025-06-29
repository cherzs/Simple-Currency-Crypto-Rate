import React, { useEffect, useRef } from "react";
import { createChart, LineSeries, CandlestickSeries } from "lightweight-charts";

export default function Chart({ 
  data, 
  width = 600, 
  height = 300, 
  title = "Chart",
  type = "line" // "line" or "candlestick"
}) {
  const chartContainerRef = useRef();

  useEffect(() => {
    if (!data || data.length === 0) return;

    const chart = createChart(chartContainerRef.current, { 
      width, 
      height,
      layout: {
        textColor: 'black',
        background: { type: 'solid', color: 'white' }
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' }
      }
    });

    if (type === "line") {
      const lineSeries = chart.addSeries(LineSeries, {
        color: '#2962FF',
        lineWidth: 2,
      });
      lineSeries.setData(data);
    } else if (type === "candlestick") {
      const candlestickSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });
      candlestickSeries.setData(data);
    }

    chart.timeScale().fitContent();

    return () => {
      chart.remove();
    };
  }, [data, width, height, type]);

  return (
    <div className="chart-container">
      <h5 className="mb-3">{title}</h5>
      <div ref={chartContainerRef} />
    </div>
  );
} 