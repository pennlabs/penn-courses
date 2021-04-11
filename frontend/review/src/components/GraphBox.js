import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { Bar } from "react-chartjs-2";

const LoadingContainer = styled.div`
  display: flex;
  width: 100%;
  height: 100%;
  justify-content: center;
  align-items: center;
  flex-direction: column;
`;

const ChartTitle = styled.div`
  font-size: 20px;
  font-weight: bold;
  text-align: center;
`;

const ChartDescription = styled.div`
  font-size: 14px;
  font-weight: normal;
  color: #b2b2b2;
  text-align: center;
`;

const sumOfSubArray = (start, end, data) => {
  let sum = 0;
  for (let i = start; i <= end; i++) {
    sum += data[i][1];
  }
  return sum;
};

const generateChartData = (data) => {
  return {
    labels: data.map((point) => Math.round(point[0] * 100) + "%"),
    datasets: [
      {
        type: "line",
        label: "5% Period Average",
        data: data.map((point, index) => {
          console.log(point[1]);
          let average;
          if (index - 5 < 0) {
            average = sumOfSubArray(0, index, data) / index;
          } else {
            average = sumOfSubArray(index - 5, index, data) / 5;
          }

          return Math.round(average * 100) / 100;
        }),
        borderColor: "#1866D2",
        borderWidth: 3,
        fill: false,
      },
      {
        type: "bar",
        label: "Demand",
        data: data.map((point) => Math.round(point[1] * 100) / 100),
        backgroundColor: "#AECBFA",
      },
    ],
  };
};

const chartOptions = {
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
    xAxes: [
      {
        display: true,
        ticks: {
          autoSkip: true,
          maxTicksLimit: 10,
          maxRotation: 0,
          minRotation: 0,
        },

        scaleLabel: {
          display: true,
          labelString: "Percentage through Add/Drop Period",
        },
      },
    ],
  },
};

const GraphBox = ({ courseCode }) => {
  const [loaded, setLoaded] = useState(false);
  const [chartData, setChartData] = useState();
  const [semester, setSemester] = useState();

  useEffect(() => {
    if (!courseCode) {
      return;
    }

    setLoaded(false);

    //TODO: Use data from ReviewPage.js so it doesnt fetch data everytime courseEval is toggled.
    fetch(`/api/review/course/${courseCode}`).then((res) =>
      res.json().then((courseResult) => {
        const demandPlot = courseResult["recent_reviews"]["pca_demand_plot"];
        console.log(demandPlot);

        if (demandPlot) {
          setSemester(courseResult["recent_reviews"]["rSemesterCalc"]);
          setChartData(generateChartData(demandPlot));
        }

        setLoaded(true);
      })
    );
  }, [courseCode]);

  return (
    <div className="box">
      {chartData ? (
        <div id="row-select-chart-container">
          <ChartTitle>
            Historical PCA Demand For {courseCode} During Add/Drop
          </ChartTitle>
          <ChartDescription>
            Based on Penn Course Alert registration averages since {semester}{" "}
            and section capacity data, normalized to a 0-4 scale.{" "}
          </ChartDescription>
          <Bar data={chartData} options={chartOptions} />
        </div>
      ) : (
        <div>
          {" "}
          {loaded ? (
            "No demand plot for this course"
          ) : (
            <LoadingContainer>
              <i
                className="fa fa-spin fa-cog fa-fw"
                style={{ fontSize: "150px", color: "#aaa" }}
              />
              <h1 style={{ fontSize: "2em", marginTop: 15 }}>Loading...</h1>
            </LoadingContainer>
          )}
        </div>
      )}
    </div>
  );
};

export default GraphBox;
