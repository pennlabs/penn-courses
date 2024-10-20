import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { defaults, Scatter } from "react-chartjs-2";

import { apiFetchPCADemandChartData } from "../utils/api";
import { toNormalizedSemester } from "../utils/helpers";
import { EVAL_GRAPH_COLORS } from "../constants/colors";

var cachedPCAChartDataResponse = null;

const LoadingContainer = styled.div`
  display: flex;
  width: 100%;
  height: 100%;
  justify-content: center;
  align-items: center;
  flex-direction: column;
`;

const ChartTitle = styled.h3`
  margin-bottom: 5px;
  vertical-align: middle;
  font-size: 20px;
`;

const ChartDescription = styled.p`
  font-size: 15px;
  font-weight: normal;
  color: #b2b2b2;
  margin-bottom: 8px;
`;

const GraphColumn = styled.div`
  padding: 15px;
  padding-top: 0px;
  padding-bottom: 0px;
  position: relative;
  width: 100%;
  flex: 0 0 100%;
  height: 100%;

  @media (min-width: 768px) {
    max-width: 50%;
    flex: 0 0 50%;
    padding-bottom: 30px;
  }
`;

const GraphRow = styled.div`
  padding: 0px 15px;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
`;

const GraphContainer = styled.div`
  padding: 35px;
  background-color: #ffffff;
  box-shadow: 0 0 14px 0 rgba(0, 0, 0, 0.07);
  margin-bottom: 30px;
  min-height: 500px;
  flex: 1;
`;

const GraphTextContainer = styled.div`
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;

  @media (min-width: 768px) {
    height: 180px;
  }

  @media (min-width: 850px) {
    height: 130px;
  }

  @media (min-width: 1080px) {
    height: 110px;
  }

  @media (min-width: 1440px) {
    height: 90px;
  }
`;

const genAverageData = seriesData => {
  const averageData = [];
  const windowSize = 0.05;
  seriesData.forEach((point, index) => {
    const xVal = point[0];
    let total = 0;
    let numInTotal = 0;
    let j = index;

    while (j >= 0 && seriesData[j][0] >= xVal - windowSize) {
      total += seriesData[j][1];
      numInTotal += 1;
      j -= 1;
    }

    const movingAverageVal = total / numInTotal;
    averageData.push({
      x: xVal * 100,
      y: movingAverageVal
    });
  });

  return averageData;
};

//PCA Demand Chart Data
const genDemandChartData = data => {
  data = data.map(([x, y]) => [x, y * 100]);
  const averageData = genAverageData(data);
  return {
    datasets: [
      {
        type: "line",
        label: "5% Moving Average",
        data: averageData,
        borderColor: EVAL_GRAPH_COLORS.DEMAND_LINE_BORDER_COLOR,
        borderWidth: 3,
        fill: false,
        linear: true
      },
      {
        type: "line",
        label: "Registration Difficulty",
        data: data.map(point => {
          return {
            x: point[0] * 100,
            y: point[1]
          };
        }),
        backgroundColor: EVAL_GRAPH_COLORS.DEMAND_FILL_BACKGROUND_COLOR,
        borderWidth: 0,
        steppedLine: true
      }
    ]
  };
};

//Percentage of Sections Open Chart Data
const genPercentChartData = data => {
  return {
    datasets: [
      {
        type: "line",
        label: "% of Sections Open",
        data: data.map(point => {
          return {
            x: point[0] * 100,
            y: point[1] * 100
          };
        }),
        borderColor: EVAL_GRAPH_COLORS.PERCENT_LINE_BORDER_COLOR,
        backgroundColor: EVAL_GRAPH_COLORS.PERCENT_FILL_BACKGROUND_COLOR,
        borderWidth: 3,
        fill: true,
        steppedLine: true
      }
    ]
  };
};

const demandChartOptions = {
  animation: false,
  tooltips: {
    mode: "index",
    intersect: false,
    backgroundColor: EVAL_GRAPH_COLORS.TOOLTIP_BACKGROUND_COLOR,
    bodyFontColor: EVAL_GRAPH_COLORS.TOOLTIP_FONT_COLOR,
    titleFontColor: EVAL_GRAPH_COLORS.TOOLTIP_FONT_COLOR,
    borderColor: EVAL_GRAPH_COLORS.TOOLTIP_BORDER_COLOR,
    borderWidth: 0.75,
    bodyFontSize: 12,
    cornerRadius: 3,
    bodySpacing: 3,
    callbacks: {
      title: (toolTipItem, data) =>
        `${Math.round(
          data["datasets"][0]["data"][toolTipItem[0]["index"]].x
        )}% Through Add/Drop`,
      beforeBody: (toolTipItem, data) =>
        `Registration Difficulty: ${Math.round(
          data["datasets"][0]["data"][toolTipItem[0]["index"]].y
        )}\n5% Moving Average: ${Math.round(
          data["datasets"][1]["data"][toolTipItem[0]["index"]].y
        )}`,
      label: () => {
        return;
      }
    }
  },
  hover: {
    mode: "nearest",
    intersect: true
  },
  elements: {
    point: {
      radius: 0
    }
  },
  legend: {
    display: true,
    position: "bottom",
    align: "start"
  },
  scales: {
    autoSkip: true,
    xAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          beginAtZero: true,
          maxTicksLimit: 6,
          stepSize: 20,
          maxRotation: 0,
          minRotation: 0,
          max: 100,
          callback: value => value + "%"
        },

        scaleLabel: {
          display: true,
          labelString: "Percent Through Add/Drop Period"
        }
      }
    ],
    yAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          maxTicksLimit: 10,
          maxRotation: 0,
          minRotation: 0,
          min: 0,
          max: 100
        }
      }
    ]
  }
};

const percentSectionChartOptions = {
  animation: false,
  tooltips: {
    mode: "index",
    intersect: false,
    backgroundColor: EVAL_GRAPH_COLORS.TOOLTIP_BACKGROUND_COLOR,
    bodyFontColor: EVAL_GRAPH_COLORS.TOOLTIP_FONT_COLOR,
    titleFontColor: EVAL_GRAPH_COLORS.TOOLTIP_FONT_COLOR,
    borderColor: EVAL_GRAPH_COLORS.TOOLTIP_BORDER_COLOR,
    borderWidth: 0.75,
    cornerRadius: 3,
    bodyFontSize: 12,
    callbacks: {
      title: (toolTipItem, data) =>
        `${Math.round(
          data["datasets"][0]["data"][toolTipItem[0]["index"]].x
        )}% Through Add/Drop`,
      beforeBody: (toolTipItem, data) =>
        `% of Sections Open: ${Math.round(
          data["datasets"][0]["data"][toolTipItem[0]["index"]].y
        )}%`,
      label: () => {
        return;
      }
    }
  },
  hover: {
    mode: "nearest",
    intersect: true
  },
  elements: {
    point: {
      radius: 0
    }
  },
  legend: {
    display: true,
    position: "bottom",
    align: "start"
  },
  scales: {
    autoSkip: true,
    xAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          beginAtZero: true,
          maxTicksLimit: 6,
          stepSize: 20,
          maxRotation: 0,
          minRotation: 0,
          max: 100,
          callback: value => value + "%"
        },

        scaleLabel: {
          display: true,
          labelString: "Percent Through Add/Drop Period"
        }
      }
    ],
    yAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          maxTicksLimit: 5,
          stepSize: 25,
          maxRotation: 0,
          minRotation: 0,
          min: 0,
          max: 100,
          callback: value => value + "%"
        }
      }
    ]
  }
};

const GraphBox = ({ courseCode, url_semester, isAverage, setIsAverage }) => {
  const averageOrRecent = isAverage ? "average_plots" : "recent_plots";

  const [chartData, setChartData] = useState(null);
  const [loaded, setLoaded] = useState(true);

  defaults.global.defaultFontFamily = "Lato";

  const handlePCAChartDataResponse = res => {
    cachedPCAChartDataResponse = res;

    const pcaDemandPlot = res[averageOrRecent]["pca_demand_plot"];
    const demandSemester =
      res[averageOrRecent]["pca_demand_plot_since_semester"];
    const percentOpenPlot = res[averageOrRecent]["percent_open_plot"];
    const percentSemester =
      res[averageOrRecent]["percent_open_plot_since_semester"];
    setChartData({
      demandSemester: demandSemester && toNormalizedSemester(demandSemester),
      demandNumSemesters: res[averageOrRecent]["pca_demand_plot_num_semesters"],
      pcaDemandChartData: pcaDemandPlot && genDemandChartData(pcaDemandPlot),
      percentSemester: percentSemester && toNormalizedSemester(percentSemester),
      percentNumSemesters:
        res[averageOrRecent]["percent_open_plot_num_semesters"],
      percentSectionsChartData:
        percentOpenPlot && genPercentChartData(percentOpenPlot)
    });
  };

  useEffect(() => {
    if (!courseCode) {
      setLoaded(true);
      setChartData(null);
      return;
    }

    if (
      cachedPCAChartDataResponse &&
      cachedPCAChartDataResponse.code === courseCode
    ) {
      handlePCAChartDataResponse(cachedPCAChartDataResponse);
    } else {
      setLoaded(false);
      apiFetchPCADemandChartData(courseCode, url_semester)
        .then(handlePCAChartDataResponse)
        .finally(() => {
          setLoaded(true);
        });
    }
  }, [courseCode, averageOrRecent, handlePCAChartDataResponse, url_semester]);

  const showPcaDemandPlotContainer =
    (chartData && chartData.pcaDemandChartData) || !loaded;
  const showPercentOpenPlotContainer =
    (chartData && chartData.percentSectionsChartData) || !loaded;

  return (
    <>
      {(showPcaDemandPlotContainer || showPercentOpenPlotContainer) && (
        <GraphRow>
          {showPcaDemandPlotContainer && (
            <GraphColumn>
              <GraphContainer>
                {chartData && chartData.pcaDemandChartData ? (
                  <div id="row-select-chart-container">
                    <GraphTextContainer>
                      <ChartTitle>
                        Estimated Registration Difficulty During Historical
                        Add/Drop Periods
                      </ChartTitle>
                      <ChartDescription>
                        Registration difficulty is estimated on a fixed 0-100
                        scale (relative to other classes at Penn), using Penn
                        Course Alert data from{" "}
                        {isAverage
                          ? `${chartData.demandNumSemesters} semesters since`
                          : ""}{" "}
                        {chartData.demandSemester}
                      </ChartDescription>
                    </GraphTextContainer>
                    <div
                      className="btn-group"
                      style={{ width: "fit-content", marginBottom: "18px" }}
                    >
                      <button
                        onClick={() => setIsAverage(true)}
                        className={`btn btn-sm ${
                          isAverage ? "btn-primary" : "btn-secondary"
                        }`}
                      >
                        Average
                      </button>
                      <button
                        onClick={() => setIsAverage(false)}
                        className={`btn btn-sm ${
                          isAverage ? "btn-secondary" : "btn-primary"
                        }`}
                      >
                        Most Recent
                      </button>
                    </div>
                    <Scatter
                      data={chartData.pcaDemandChartData}
                      options={demandChartOptions}
                    />
                  </div>
                ) : (
                  <div>
                    {" "}
                    {loaded || (
                      <LoadingContainer>
                        <i
                          className="fa fa-spin fa-cog fa-fw"
                          style={{ fontSize: "150px", color: "#aaa" }}
                        />
                        <h1 style={{ fontSize: "2em", marginTop: 15 }}>
                          Loading...
                        </h1>
                      </LoadingContainer>
                    )}
                  </div>
                )}
              </GraphContainer>
            </GraphColumn>
          )}
          {showPercentOpenPlotContainer && (
            <GraphColumn>
              <GraphContainer>
                {chartData && chartData.percentSectionsChartData ? (
                  <div id="row-select-chart-container">
                    <GraphTextContainer>
                      <ChartTitle>
                        Percent of Sections Open During Historical Add/Drop
                        Periods
                      </ChartTitle>
                      <ChartDescription>
                        Based on section status data during add/drop periods
                        from
                        {isAverage
                          ? ` ${chartData.percentNumSemesters} semesters since`
                          : ""}
                        {" " + chartData.percentSemester}
                      </ChartDescription>
                    </GraphTextContainer>
                    <div
                      className="btn-group"
                      style={{ width: "fit-content", marginBottom: "18px" }}
                    >
                      <button
                        onClick={() => setIsAverage(true)}
                        className={`btn btn-sm ${
                          isAverage ? "btn-primary" : "btn-secondary"
                        }`}
                      >
                        Average
                      </button>
                      <button
                        onClick={() => setIsAverage(false)}
                        className={`btn btn-sm ${
                          isAverage ? "btn-secondary" : "btn-primary"
                        }`}
                      >
                        Most Recent
                      </button>
                    </div>
                    <Scatter
                      data={chartData.percentSectionsChartData}
                      options={percentSectionChartOptions}
                    />
                  </div>
                ) : (
                  <div>
                    {" "}
                    {loaded || (
                      <LoadingContainer>
                        <i
                          className="fa fa-spin fa-cog fa-fw"
                          style={{ fontSize: "150px", color: "#aaa" }}
                        />
                        <h1 style={{ fontSize: "2em", marginTop: 15 }}>
                          Loading...
                        </h1>
                      </LoadingContainer>
                    )}
                  </div>
                )}
              </GraphContainer>
            </GraphColumn>
          )}
        </GraphRow>
      )}
    </>
  );
};

export default GraphBox;
