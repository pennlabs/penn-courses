import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { defaults, Scatter } from "react-chartjs-2";
import ReactTooltip from "react-tooltip";

import { toNormalizedSemester } from "../utils/helpers";
import { EVAL_GRAPH_COLORS } from "../constants/colors";

const addDropDate = [];

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
`;

const ChartDescription = styled.p`
  font-size: 12px;
  font-weight: normal;
  color: #b2b2b2;
  margin-bottom: 8px;
`;

const FilterText = styled.h3`
  font-size: 12px;
  margin: 0px;
`;

const EmptyGraphContainer = styled.div`
  padding: 10px;
  text-align: center;
  color: #8a8a8a;
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
    height: 140px;
  }
`;

const genAverageData = (seriesData) => {
  const averageData = [];
  const windowSize = 0.05;
  seriesData.map((point, index) => {
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
      x: (xVal * 100).toFixed(2),
      y: movingAverageVal.toFixed(2),
    });
  });

  return averageData;
};

//PCA Demand Chart Data
const genDemandChartData = (data, averageData) => {
  return {
    datasets: [
      {
        type: "line",
        label: "5% Moving Average",
        data: averageData,
        borderColor: EVAL_GRAPH_COLORS.DEMAND_LINE_BORDER_COLOR,
        borderWidth: 3,
        fill: false,
        linear: true,
      },
      {
        type: "line",
        label: "Registration Difficulty",
        data: data.map((point) => {
          return {
            x: (point[0] * 100).toFixed(2),
            y: Math.round(point[1] * 100) / 100,
          };
        }),
        backgroundColor: EVAL_GRAPH_COLORS.DEMAND_FILL_BACKGROUND_COLOR,
        borderWidth: 0,
        steppedLine: true,
      },
    ],
  };
};

//Percentage of Sections Open Chart Data
const genPercentChartData = (data) => {
  return {
    datasets: [
      {
        type: "line",
        label: "% of Sections Open",
        data: data.map((point) => {
          return {
            x: Math.round((point[0] * 100).toFixed()),
            y: Math.round(point[1] * 100),
          };
        }),
        borderColor: EVAL_GRAPH_COLORS.PERCENT_LINE_BORDER_COLOR,
        backgroundColor: EVAL_GRAPH_COLORS.PERCENT_FILL_BACKGROUND_COLOR,
        borderWidth: 3,
        fill: true,
        steppedLine: true,
      },
    ],
  };
};

const demandChartOptions = {
  tooltips: {
    mode: "index",
    intersect: false,
    backgroundColor: EVAL_GRAPH_COLORS.TOOLTIP_BACKGROUND_COLOR,
    bodyFontColor: EVAL_GRAPH_COLORS.TOOLTIP_FONT_COLOR,
    titleFontColor: EVAL_GRAPH_COLORS.TOOLTIP_FONT_COLOR,
    bodyFontSize: 12,
    cornerRadius: 3,
    bodySpacing: 3,
    callbacks: {
      title: (toolTipItem, data) =>
        `${
          data["datasets"][0]["data"][toolTipItem[0]["index"]].x
        }% Through Add/Drop`,
      beforeBody: (toolTipItem, data) =>
        `Projected Date: ${calcApproxDate(
          addDropDate[0],
          addDropDate[1],
          data["datasets"][0]["data"][toolTipItem[0]["index"]].x / 100
        )}\nRegistration Difficulty: ${
          data["datasets"][0]["data"][toolTipItem[0]["index"]].y
        }\n5% Moving Average: ${
          data["datasets"][1]["data"][toolTipItem[0]["index"]].y
        }`,
      label: () => {
        return;
      },
    },
  },
  hover: {
    mode: "nearest",
    intersect: true,
  },
  elements: {
    point: {
      radius: 0,
    },
  },
  legend: {
    display: true,
    position: "bottom",
    align: "start",
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
          callback: (value) => value + "%",
        },

        scaleLabel: {
          display: true,
          labelString: "Percent Through Add/Drop Period",
        },
      },
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
          max: 1,
        },
      },
    ],
  },
};

const percentSectionChartOptions = {
  tooltips: {
    mode: "index",
    intersect: false,
    backgroundColor: EVAL_GRAPH_COLORS.TOOLTIP_BACKGROUND_COLOR,
    bodyFontColor: EVAL_GRAPH_COLORS.TOOLTIP_FONT_COLOR,
    titleFontColor: EVAL_GRAPH_COLORS.TOOLTIP_FONT_COLOR,
    cornerRadius: 3,
    bodyFontSize: 12,
    callbacks: {
      title: (toolTipItem, data) =>
        `${
          data["datasets"][0]["data"][toolTipItem[0]["index"]].x
        }% Through Add/Drop`,
      beforeBody: (toolTipItem, data) =>
        `Projected Date: ${calcApproxDate(
          addDropDate[0],
          addDropDate[1],
          data["datasets"][0]["data"][toolTipItem[0]["index"]].x / 100
        )}\n% of Sections Open: ${
          data["datasets"][0]["data"][toolTipItem[0]["index"]].y
        }%`,
      label: () => {
        return;
      },
    },
  },
  hover: {
    mode: "nearest",
    intersect: true,
  },
  elements: {
    point: {
      radius: 0,
    },
  },
  legend: {
    display: true,
    position: "bottom",
    align: "start",
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
          callback: (value) => value + "%",
        },

        scaleLabel: {
          display: true,
          labelString: "Percent Through Add/Drop Period",
        },
      },
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
          callback: (value) => value + "%",
        },
      },
    ],
  },
};

const calcApproxDate = (startDateString, endDateString, percent) => {
  const startDate = new Date(startDateString);
  const endDate = new Date(endDateString);

  const percentageThrough = (endDate.getTime() - startDate.getTime()) * percent;
  const approxDate = new Date(startDate.getTime() + percentageThrough);

  return approxDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

const GraphBox = ({ courseCode, courseData, isAverage }) => {
  const [loaded, setLoaded] = useState(false);
  const [pcaDemandChartData, setPCADemandChartData] = useState(null);
  const [percentSectionsChartData, setPercentSectionsChartData] = useState(
    null
  );

  const averageOrRecent = isAverage ? "average_reviews" : "recent_reviews";
  const demandSemester =
    courseData[averageOrRecent]["pca_demand_plot_since_semester"];
  const percentSemester =
    courseData[averageOrRecent]["percent_open_plot_since_semester"];

  defaults.global.defaultFontFamily = "Lato";

  useEffect(() => {
    if (!courseCode) {
      return;
    }

    setLoaded(false);

    addDropDate.push(courseData["current_add_drop_period"].start);
    addDropDate.push(courseData["current_add_drop_period"].end);

    //Generate demand plot data
    const pcaDemandPlot = courseData[averageOrRecent]["pca_demand_plot"];
    if (pcaDemandPlot) {
      const averageData = genAverageData(pcaDemandPlot);
      setPCADemandChartData(genDemandChartData(pcaDemandPlot, averageData));
    } else {
      setPCADemandChartData(null);
    }

    //Generate percent of sections open  plot data
    const percentSectionsPlot =
      courseData[averageOrRecent]["percent_open_plot"];

    if (percentSectionsPlot) {
      setPercentSectionsChartData(genPercentChartData(percentSectionsPlot));
    } else {
      setPCADemandChartData(null);
    }

    setLoaded(true);
  }, [courseCode]);

  return (
    <>
      <GraphRow>
        <GraphColumn>
          <GraphContainer>
            {pcaDemandChartData ? (
              <div id="row-select-chart-container">
                <GraphTextContainer>
                  <ChartTitle>
                    Historically, how difficult has it been to get into{" "}
                    {courseCode} during the add/drop period?
                    <a data-tip data-for="demandInfo">
                      {" "}
                      <i
                        className="fa fa-question-circle"
                        style={{ color: "#c6c6c6", fontSize: "13px" }}
                      />
                    </a>
                    <ReactTooltip
                      id="demandInfo"
                      place="top"
                      type="light"
                      effect="solid"
                    >
                      <span>Test test test</span>
                    </ReactTooltip>
                  </ChartTitle>
                  <ChartDescription>
                    Registration difficulty is represented on a 0-1 scale
                    (relative to other classes at Penn), plotted over time as a
                    % of add/drop period elapsed, using Penn Course Alert data
                    from semesters since{" "}
                    {" " + toNormalizedSemester(demandSemester)})
                  </ChartDescription>
                  <FilterText>
                    Filter By:{" "}
                    {isAverage ? "All Semesters" : "Most Recent Semester"}
                  </FilterText>
                </GraphTextContainer>
                <Scatter
                  data={pcaDemandChartData}
                  options={demandChartOptions}
                />
              </div>
            ) : (
              <div>
                {" "}
                {loaded ? (
                  <EmptyGraphContainer>
                    All underlying sections either have no data to show, or
                    require permits for registration (we cannot estimate the
                    difficulty of being issued a permit).
                  </EmptyGraphContainer>
                ) : (
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
        <GraphColumn>
          <GraphContainer>
            {percentSectionsChartData ? (
              <div id="row-select-chart-container">
                <GraphTextContainer>
                  <ChartTitle>
                    Percent of historical {courseCode} sections open during the
                    add/drop period
                  </ChartTitle>
                  <ChartDescription>
                    Based on section status update data during add/drop periods
                    since {" " + toNormalizedSemester(percentSemester)}
                  </ChartDescription>
                  <FilterText>
                    Filter By:{" "}
                    {isAverage ? "All Semesters" : "Most Recent Semester"}
                  </FilterText>
                </GraphTextContainer>
                <Scatter
                  data={percentSectionsChartData}
                  options={percentSectionChartOptions}
                />
              </div>
            ) : (
              <div>
                {" "}
                {loaded ? (
                  <EmptyGraphContainer>
                    All underlying sections either have no data to show, or
                    require permits for registration (we cannot estimate the
                    difficulty of being issued a permit).
                  </EmptyGraphContainer>
                ) : (
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
      </GraphRow>
    </>
  );
};

export default GraphBox;
