import React, { useEffect, useState } from "react";
import { PERCENTAGE_COLUMNS } from "../../constants/values";
import ReactTable from "react-table";

export const ScoreTable = (props) => {
  const {
    alternating = false,
    noun,
    multi,
    data = [],
    onSelect = () => {},
    isAverage = null,
    isCourseEval = null,
  } = props;
  const [selected, setSelected] = useState(multi ? {} : null);
  const [sorted, setSorted] = useState(props.sorted);

  // Force rerender of table content when isAverage changes
  // TODO: Move isAverage into localstorage or redux store
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setSorted([...sorted]), [isAverage, isCourseEval]);
  useEffect(() => {
    const selected = multi ? {} : null;
    setSelected(selected);
    onSelect && onSelect(selected);
  }, [data, multi, onSelect]);

  const getTrProps = (_, rowInfo) => {
    const { index, original, row } = rowInfo;
    const noRow = multi ? index in selected : index === selected;
    return rowInfo && row
      ? {
          style: alternating
            ? { backgroundColor: row._viewIndex % 2 ? "#F5F8F8" : "white" }
            : {},
          onClick: () => {
            // Recalculate value every time onClick is called
            const noRow = multi ? index in selected : index === selected;
            if (!multi) {
              const { key } = original;
              onSelect(noRow ? null : key);
              setSelected(noRow ? null : index);
              return;
            }
            if (noRow) {
              delete selected[index];
            } else {
              selected[index] = rowInfo;
            }
            onSelect(selected);
            setSelected({ ...selected });
          },
          className: noRow ? "selected" : "",
        }
      : {};
  };

  // Convert relevant columns to percentages
  data.forEach((row) => {
    PERCENTAGE_COLUMNS.forEach((title) => {
      if (row[title] && row[title].average) {
        row[title].average =
          row[title].average.slice(-1) === "%"
            ? row[title].average
            : `${Math.floor(parseFloat(row[title].average) * 100)}%`;
      }
      if (row[title] && row[title].recent) {
        row[title].recent =
          row[title].recent.slice(-1) === "%"
            ? row[title].recent
            : `${Math.floor(parseFloat(row[title].recent) * 100)}%`;
      }
      // if (!isNaN(row[title])) {
      //   row[title] = Math.floor(parseInt(row[title]) * 100);
      // }
    });
  });
  console.log(data);

  return (
    <div>
      <ReactTable
        className="mb-2"
        {...props}
        showPagination={false}
        resizable={false}
        style={{ maxHeight: 400 }}
        getTrProps={getTrProps}
        minRows={0}
        pageSize={data.length}
        sorted={sorted}
        onSortedChange={setSorted}
      />
      <span id="course-table_info">
        Showing {data.length} {(noun || "row") + (data.length !== 1 ? "s" : "")}
      </span>
    </div>
  );
};
