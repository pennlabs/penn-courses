import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { Bar, Scatter } from "react-chartjs-2";

let addDropDate = [];

const LoadingContainer = styled.div`
  display: flex;
  width: 100%;
  height: 100%;
  justify-content: center;
  align-items: center;
  flex-direction: column;
`;

const ChartTitle = styled.div`
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 5px;
`;

const ChartDescription = styled.div`
  font-size: 12px;
  font-weight: normal;
  color: #b2b2b2;
  margin-bottom: 10px;
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
`;

const genAverageData = (seriesData) => {
  let averageData = [];
  let windowSize = 0.05;
  for (let i = 0; i < seriesData.length; i++) {
    let xVal = seriesData[i][0];
    let total = 0;
    let numInTotal = 0;
    let j = i;
    while (j >= 0 && seriesData[j][0] >= xVal - windowSize) {
      total += seriesData[j][1];
      numInTotal += 1;
      j -= 1;
    }
    let movingAverageVal = total / numInTotal;
    averageData.push({
      x: (xVal * 100).toFixed(2),
      y: movingAverageVal.toFixed(2),
    });
  }

  return averageData;
};

//PCA Demand Chart Data
const genDemandChartData = (data, averageData) => {
  return {
    datasets: [
      {
        type: "line",
        label: "5% Period Average",
        data: averageData,
        borderColor: "#6378E9",
        borderWidth: 3,
        fill: false,
        linear: true,
      },
      {
        type: "line",
        label: "Difficulty",
        data: data.map((point) => {
          return {
            x: (point[0] * 100).toFixed(2),
            y: Math.round(point[1] * 100) / 100,
          };
        }),
        backgroundColor: "#AAACEC",
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
        label: "% of Section Open",
        data: data.map((point) => {
          return {
            x: Math.round((point[0] * 100).toFixed()),
            y: Math.round(point[1] * 100),
          };
        }),
        borderColor: "#87BD99",
        backgroundColor: "#E0EBEC",
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
    backgroundColor: "#deebff",
    bodyFontColor: "#000000",
    titleFontColor: "#000000",
    bodyFontSize: 12,
    callbacks: {
      title: (toolTipItem, data) => {
        return (
          "Time: " +
          data["datasets"][0]["data"][toolTipItem[0]["index"]].x +
          "%"
        );
      },
      beforeBody: (toolTipItem, data) => {
        let bodyText = "";
        bodyText +=
          "Approx Date: " +
          calcApproxDate(
            addDropDate.start,
            addDropDate.end,
            data["datasets"][0]["data"][toolTipItem[0]["index"]].x / 100
          ) +
          "\n";
        bodyText +=
          "Difficulty: " +
          data["datasets"][0]["data"][toolTipItem[0]["index"]].y +
          "\n";
        bodyText +=
          "5% Period Avg: " +
          data["datasets"][1]["data"][toolTipItem[0]["index"]].y +
          "\n";
        return bodyText;
      },
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
          maxTicksLimit: 12,
          stepSize: 10,
          maxRotation: 0,
          minRotation: 0,
          max: 100,
          callback: function(value) {
            return value + "%";
          },
        },

        scaleLabel: {
          display: true,
          labelString: "Percentage through Add/Drop Period",
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
    backgroundColor: "#deebff",
    bodyFontColor: "#000000",
    titleFontColor: "#000000",
    bodyFontSize: 12,
    callbacks: {
      title: (toolTipItem, data) => {
        return (
          "Time: " +
          data["datasets"][0]["data"][toolTipItem[0]["index"]].x +
          "%"
        );
      },
      beforeBody: (toolTipItem, data) => {
        let bodyText = "";
        bodyText +=
          "Approx Date: " +
          calcApproxDate(
            addDropDate.start,
            addDropDate.end,
            data["datasets"][0]["data"][toolTipItem[0]["index"]].x / 100
          ) +
          "\n";
        bodyText +=
          "% of Section Open: " +
          data["datasets"][0]["data"][toolTipItem[0]["index"]].y +
          "%\n";
        return bodyText;
      },
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
          callback: (value) => {
            return value + "%";
          },
        },

        scaleLabel: {
          display: true,
          labelString: "Percentage through Add/Drop Period",
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
          callback: (value) => {
            return value + "%";
          },
        },
      },
    ],
  },
};

const translateSemester = (semester) => {
  const year = semester.substring(0, 4);
  const season = semester.substring(4);
  if (season === "A") {
    return "Spring " + year;
  } else if (season === "B") {
    return "Summer " + year;
  } else if (season === "C") {
    return "Fall " + year;
  }
  return year;
};

const calcApproxDate = (startDateString, endDateString, percent) => {
  let startDate = new Date(startDateString);
  let endDate = new Date(endDateString);

  let percentageThrough = (endDate.getTime() - startDate.getTime()) * percent;
  let approxDate = new Date(startDate.getTime() + percentageThrough);

  return approxDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

const GraphBox = ({ courseCode, courseData, isAverage }) => {
  const [loaded, setLoaded] = useState(false);
  const [pcaDemandChartData, setPCADemandChartData] = useState();
  const [percentSectionsChartData, setPercentSectionsChartData] = useState();
  const [semester, setSemester] = useState();

  useEffect(() => {
    if (!courseCode) {
      return;
    }

    setLoaded(false);

    const averageOrRecent = isAverage ? "average_reviews" : "recent_reviews";

    setSemester(courseData[averageOrRecent]["rSemesterCalc"]);
    addDropDate = courseData["current_add_drop_period"];
    console.log(addDropDate);

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
                <ChartTitle>
                  Historically, how difficult has it been to get into{" "}
                  {courseCode} during the add/drop period?
                </ChartTitle>
                <ChartDescription>
                  'Difficulty' is represented on a 0-1 scale (relative to all
                  classes at Penn), plotted over time as a % of add/drop period
                  elapsed, using Penn Course Alert data from semesters since{" "}
                  {translateSemester(semester)})
                </ChartDescription>
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
                <ChartTitle>
                  Percent of sections open for {courseCode} during the add/drop
                  period
                </ChartTitle>
                <ChartDescription>
                  Based on Penn inTouch registration data since{" "}
                  {translateSemester(semester)}. Calculated by number of
                  sections open divided by the total number of sections.
                </ChartDescription>
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
